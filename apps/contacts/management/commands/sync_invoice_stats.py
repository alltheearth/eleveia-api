# apps/contacts/management/commands/sync_invoice_stats.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from apps.schools.models import School
import requests
import sys


class Command(BaseCommand):
    help = 'Pré-carrega cache de boletos de todas as escolas'

    def add_arguments(self, parser):
        parser.add_argument('--school-id', type=int, help='ID de escola específica')
        parser.add_argument('--verbose', action='store_true', help='Modo detalhado')

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.verbose = options.get('verbose', False)
        school_id = options.get('school_id')

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 SINCRONIZAÇÃO DE BOLETOS - PRÉ-CACHE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'⏰ Início: {start_time.strftime("%Y-%m-%d %H:%M:%S")}\n')

        # Buscar escolas
        if school_id:
            try:
                schools = [School.objects.get(id=school_id)]
                self.stdout.write(f'🏫 Escola: {schools[0].school_name}\n')
            except School.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Escola {school_id} não encontrada'))
                sys.exit(1)
        else:
            schools = School.objects.filter(
                application_token__isnull=False
            ).exclude(application_token='')
            self.stdout.write(f'🏫 {len(schools)} escola(s) com token\n')

        if not schools:
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma escola com token'))
            return

        # Processar cada escola
        success_count = 0
        error_count = 0

        for idx, school in enumerate(schools, 1):
            self.stdout.write('-' * 70)
            self.stdout.write(f'[{idx}/{len(schools)}] 🏫 {school.school_name} (ID: {school.id})')

            try:
                invoices_data = self._process_school(school)

                # 💾 SALVAR NO CACHE
                cache_key = f"all_invoices_school_{school.id}"
                cache.set(cache_key, invoices_data, timeout=3600)  # 1 hora

                self.stdout.write(self.style.SUCCESS(
                    f'✅ {invoices_data["summary"]["total_students"]} alunos, '
                    f'{invoices_data["summary"]["total_invoices"]} boletos cacheados'
                ))
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erro: {str(e)}'))
                error_count += 1
                if self.verbose:
                    import traceback
                    self.stdout.write(traceback.format_exc())

        # Resumo
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('📊 RESUMO'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'✅ Sucesso: {success_count}')
        self.stdout.write(f'❌ Erros: {error_count}')
        self.stdout.write(f'⏱️  Tempo: {duration:.2f}s')
        self.stdout.write('=' * 70 + '\n')

    def _process_school(self, school):
        """Busca e processa todos os boletos da escola"""

        # 1️⃣ Buscar alunos
        if self.verbose:
            self.stdout.write('   📚 Buscando alunos...')

        students = self._fetch_students(school.application_token)

        if self.verbose:
            self.stdout.write(f'   ✓ {len(students)} alunos')

        # 2️⃣ Buscar boletos de cada aluno
        if self.verbose:
            self.stdout.write('   💰 Buscando boletos...')

        all_invoices = []
        students_with_invoices = []

        headers = {
            "Authorization": f"Bearer {school.application_token}",
            "Content-Type": "application/json"
        }

        for idx, student in enumerate(students, 1):
            student_id = student.get('id')
            if not student_id:
                continue

            if self.verbose and idx % 50 == 0:
                self.stdout.write(f'      {idx}/{len(students)} alunos...')

            try:
                url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
                params = {'id_aluno': student_id}

                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    invoices = data.get('resultados', [])

                    if invoices:
                        student_invoices = {
                            'student_id': student_id,
                            'student_name': student.get('nome'),
                            'student_registration': student.get('matricula'),
                            'student_class': invoices[0].get('turma') if invoices else None,
                            'invoices': []
                        }

                        for invoice in invoices:
                            invoice_data = {
                                "invoice_number": invoice.get("titulo"),
                                "bank": invoice.get("nome_banco"),
                                "due_date": invoice.get("dt_vencimento"),
                                "payment_date": invoice.get("dt_pagamento"),
                                "total_amount": invoice.get("valor_documento"),
                                "received_amount": invoice.get("valor_recebido_total"),
                                "status_code": invoice.get("situacao_titulo"),
                                "installment": invoice.get("parcela_cobranca"),
                                "digitable_line": invoice.get("linha_digitavel"),
                                "payment_url": invoice.get("link_pagamento"),
                            }
                            student_invoices['invoices'].append(invoice_data)
                            all_invoices.append(invoice_data)

                        students_with_invoices.append(student_invoices)

            except requests.exceptions.RequestException:
                continue

        # 3️⃣ Calcular estatísticas
        total_invoices = len(all_invoices)
        paid = sum(1 for inv in all_invoices if inv['status_code'] == 'LIQ')
        pending = total_invoices - paid

        return {
            'students': students_with_invoices,
            'summary': {
                'total_students': len(students_with_invoices),
                'total_invoices': total_invoices,
                'paid_count': paid,
                'pending_count': pending,
                'completion_rate': round((paid / total_invoices * 100), 2) if total_invoices > 0 else 0,
            },
            'last_updated': timezone.now().isoformat(),
        }

    def _fetch_students(self, token):
        """Busca todos os alunos"""
        url = "https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        all_students = []
        next_url = url

        while next_url:
            response = requests.get(next_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                all_students.extend(data)
                break
            elif isinstance(data, dict):
                all_students.extend(data.get('results', []))
                next_url = data.get('next')
            else:
                break

        return all_students