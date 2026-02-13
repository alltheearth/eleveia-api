# apps/contacts/management/commands/diagnostico_boletos.py
"""
Comando Django para diagnosticar problemas com boletos
VERSÃO CORRIGIDA - Funciona sem Redis

COMO USAR:
    python manage.py diagnostico_boletos

    # Com escola específica
    python manage.py diagnostico_boletos --school-id 2

    # Sem tentar limpar cache (se Redis não estiver rodando)
    python manage.py diagnostico_boletos --no-cache
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from apps.schools.models import School
import requests

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback sem cores
    class Fore:
        CYAN = RED = GREEN = YELLOW = ''
    class Style:
        RESET_ALL = ''


class Command(BaseCommand):
    help = 'Diagnostica problemas com a integração de boletos SIGA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            help='ID da escola para testar (padrão: primeira escola encontrada)'
        )
        parser.add_argument(
            '--no-cache',
            action='store_true',
            help='Não tentar limpar cache (útil se Redis não estiver rodando)'
        )
        parser.add_argument(
            '--test-students',
            type=int,
            default=10,
            help='Número de alunos para testar (padrão: 10)'
        )

    def handle(self, *args, **options):
        self.verbose = options['verbosity'] > 1
        school_id = options.get('school_id')
        no_cache = options.get('no_cache')
        test_students = options.get('test_students', 10)

        self.stdout.write("\n" + "="*70)
        self.stdout.write(Fore.CYAN + "🔍 DIAGNÓSTICO DE BOLETOS - INTEGRAÇÃO SIGA")
        self.stdout.write("="*70 + "\n")

        # Limpar cache se solicitado e possível
        if not no_cache:
            try:
                cache.clear()
                self.stdout.write(Fore.GREEN + "✓ Cache limpo\n")
            except Exception as e:
                self.stdout.write(Fore.YELLOW + f"⚠️  Não foi possível limpar cache (Redis offline?): {str(e)[:50]}")
                self.stdout.write(Fore.YELLOW + "   Continuando sem cache...\n")

        # ========================================
        # 1. VERIFICAR ESCOLA
        # ========================================
        self.stdout.write(Fore.YELLOW + "1️⃣ VERIFICANDO ESCOLA\n")

        try:
            if school_id:
                school = School.objects.get(id=school_id)
            else:
                school = School.objects.first()

            if not school:
                self.stdout.write(Fore.RED + "❌ Nenhuma escola encontrada!")
                return

            self.stdout.write(f"   Escola: {school.school_name} (ID: {school.id})")

            if not school.application_token:
                self.stdout.write(Fore.RED + "\n   ❌ ERRO: Token não configurado!")
                self.stdout.write("\n   Configure o 'application_token' no admin")
                return

            self.stdout.write(Fore.GREEN + f"   ✓ Token configurado ({len(school.application_token)} caracteres)\n")

        except School.DoesNotExist:
            self.stdout.write(Fore.RED + f"❌ Escola com ID {school_id} não encontrada!")
            return

        # ========================================
        # 2. TESTAR CONEXÃO
        # ========================================
        self.stdout.write(Fore.YELLOW + "2️⃣ TESTANDO CONEXÃO COM SIGA\n")

        headers = {
            "Authorization": f"Bearer {school.application_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(
                "https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/",
                headers=headers,
                timeout=30
            )

            if response.status_code == 401:
                self.stdout.write(Fore.RED + "   ❌ Token inválido ou expirado!")
                return
            elif response.status_code == 403:
                self.stdout.write(Fore.RED + "   ❌ Token sem permissão!")
                return
            elif response.status_code != 200:
                self.stdout.write(Fore.RED + f"   ❌ Erro {response.status_code}")
                return

            self.stdout.write(Fore.GREEN + "   ✓ Conexão OK\n")

        except requests.exceptions.Timeout:
            self.stdout.write(Fore.RED + "   ❌ Timeout na conexão")
            return
        except requests.exceptions.ConnectionError:
            self.stdout.write(Fore.RED + "   ❌ Erro de conexão")
            return

        # ========================================
        # 3. VERIFICAR ALUNOS
        # ========================================
        self.stdout.write(Fore.YELLOW + "3️⃣ VERIFICANDO ALUNOS\n")

        try:
            data = response.json()

            if isinstance(data, list):
                students = data
            elif isinstance(data, dict):
                students = data.get('results', [])
            else:
                self.stdout.write(Fore.RED + "   ❌ Formato de resposta inválido")
                return

            self.stdout.write(f"   Total de alunos: {len(students)}")

            if len(students) == 0:
                self.stdout.write(Fore.RED + "\n   ⚠️ Nenhum aluno encontrado!\n")
                return

            # Mostrar exemplos
            if self.verbose:
                self.stdout.write(f"\n   Primeiros 5 alunos:")
                for i, s in enumerate(students[:5], 1):
                    name = s.get('nome', 'N/A')
                    sid = s.get('id', 'N/A')
                    self.stdout.write(f"   [{i}] {name[:40]:<40} ID: {sid}")

            self.stdout.write()

        except Exception as e:
            self.stdout.write(Fore.RED + f"   ❌ Erro: {e}\n")
            return

        # ========================================
        # 4. TESTAR BOLETOS
        # ========================================
        self.stdout.write(Fore.YELLOW + f"4️⃣ TESTANDO BOLETOS ({test_students} alunos)\n")

        with_invoices = 0
        without_invoices = 0
        total_invoices = 0
        errors = 0

        self.stdout.write(f"\n   {'Aluno':<40} {'Boletos':<10} {'Status'}")
        self.stdout.write("   " + "-"*65)

        for i, student in enumerate(students[:test_students], 1):
            student_id = student.get('id')
            student_name = student.get('nome', 'N/A')[:40]

            if not student_id:
                self.stdout.write(Fore.RED + f"   [{i:2d}] {student_name:<40} {'N/A':<10} ❌")
                errors += 1
                continue

            try:
                r = requests.get(
                    "https://siga.activesoft.com.br/api/v0/informacoes_boleto/",
                    headers=headers,
                    params={'id_aluno': student_id},
                    timeout=10
                )

                if r.status_code == 200:
                    inv_data = r.json()
                    invoices = inv_data.get('resultados', [])
                    num = len(invoices)

                    if num > 0:
                        with_invoices += 1
                        total_invoices += num

                        paid = sum(1 for inv in invoices if inv.get('situacao_titulo') == 'LIQ')
                        pending = num - paid

                        self.stdout.write(
                            Fore.GREEN +
                            f"   [{i:2d}] {student_name:<40} {num:<10} "
                            f"✓ ({paid} pagos, {pending} pendentes)"
                        )
                    else:
                        without_invoices += 1
                        self.stdout.write(
                            Fore.YELLOW +
                            f"   [{i:2d}] {student_name:<40} {0:<10} ⚠️ Sem boletos"
                        )
                else:
                    errors += 1
                    self.stdout.write(
                        Fore.RED +
                        f"   [{i:2d}] {student_name:<40} {'ERRO':<10} ❌ {r.status_code}"
                    )

            except requests.exceptions.Timeout:
                errors += 1
                self.stdout.write(
                    Fore.RED +
                    f"   [{i:2d}] {student_name:<40} {'TIMEOUT':<10} ⏱️"
                )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    Fore.RED +
                    f"   [{i:2d}] {student_name:<40} {'ERRO':<10} ❌"
                )

        # ========================================
        # 5. VERIFICAR CACHE
        # ========================================
        self.stdout.write("\n" + Fore.YELLOW + "5️⃣ VERIFICANDO CACHE\n")

        if no_cache:
            self.stdout.write("   Cache desabilitado (--no-cache)")
        else:
            try:
                cache_key = f"all_invoices_school_{school.id}"
                cached_data = cache.get(cache_key)

                if cached_data:
                    self.stdout.write(Fore.GREEN + "   ✓ Dados em cache encontrados")
                    self.stdout.write(f"   • Alunos: {cached_data['summary']['total_students']}")
                    self.stdout.write(f"   • Boletos: {cached_data['summary']['total_invoices']}")
                    self.stdout.write(f"   • Atualizado: {cached_data['last_updated']}")
                else:
                    self.stdout.write("   Sem dados em cache")
            except Exception as e:
                self.stdout.write(Fore.YELLOW + f"   ⚠️ Erro ao verificar cache: {str(e)[:50]}")
                self.stdout.write(Fore.YELLOW + "   (Redis pode estar offline)")

        # ========================================
        # 6. RESUMO
        # ========================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write(Fore.CYAN + "📊 RESUMO")
        self.stdout.write("="*70 + "\n")

        self.stdout.write(f"Total de alunos: {len(students)}")
        self.stdout.write(f"Alunos testados: {test_students}")
        self.stdout.write(f"  • Com boletos: {with_invoices}")
        self.stdout.write(f"  • Sem boletos: {without_invoices}")
        self.stdout.write(f"  • Erros: {errors}")
        self.stdout.write(f"Total de boletos: {total_invoices}")

        if total_invoices > 0:
            avg = total_invoices / with_invoices if with_invoices > 0 else 0
            self.stdout.write(f"Média: {avg:.1f} boletos/aluno")

        # ========================================
        # 7. DIAGNÓSTICO FINAL
        # ========================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write(Fore.CYAN + "🎯 DIAGNÓSTICO FINAL")
        self.stdout.write("="*70 + "\n")

        if with_invoices > 0:
            self.stdout.write(Fore.GREEN + "✅ INTEGRAÇÃO FUNCIONANDO!\n")
            self.stdout.write(f"A API retornou {total_invoices} boletos de {with_invoices} alunos.\n")
            self.stdout.write(Fore.YELLOW + "⚠️  SE A ROTA AINDA RETORNA VAZIO:\n")
            self.stdout.write("1. Substitua a view pela versão corrigida:")
            self.stdout.write("   cp student_invoice_views_FIXED.py apps/contacts/views/student_invoice_views.py")
            self.stdout.write("2. Reinicie o Django (Ctrl+C e runserver novamente)")
            self.stdout.write("3. Teste a rota: GET /api/contacts/students/invoices/")

        elif with_invoices == 0 and without_invoices > 0:
            self.stdout.write(Fore.RED + "❌ PROBLEMA: Nenhum aluno possui boletos!\n")
            self.stdout.write("Possíveis causas:")
            self.stdout.write("1. Boletos não cadastrados no SIGA")
            self.stdout.write("2. Filtro de período/ano na API")

        elif errors > 0:
            self.stdout.write(Fore.YELLOW + "⚠️ PROBLEMAS DE CONECTIVIDADE\n")
            self.stdout.write(f"Ocorreram {errors} erros ao buscar boletos.")

        self.stdout.write("\n" + "="*70 + "\n")