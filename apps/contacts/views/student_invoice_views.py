# apps/contacts/views_new.py

from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.utils import timezone
from core.permissions import IsSchoolStaff
from collections import defaultdict


class StudentInvoiceView(APIView):
    """Busca TODOS os boletos de TODOS os alunos da escola (com cache e paralelização)"""
    permission_classes = [IsSchoolStaff]

    def get(self, request):
        # Validação
        if not hasattr(request.user, 'profile'):
            return Response({"error": "Usuário sem perfil"}, status=status.HTTP_403_FORBIDDEN)

        if not request.user.profile.school:
            return Response({"error": "Usuário sem escola vinculada"}, status=status.HTTP_403_FORBIDDEN)

        school = request.user.profile.school

        if not school.application_token:
            return Response({"error": "Escola sem token configurado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Cache (1 hora)
        cache_key = f"all_invoices_school_{school.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response({
                **cached_data,
                'cached': True,
                'cache_info': 'Dados do cache (atualizados a cada 1 hora)'
            }, status=status.HTTP_200_OK)

        # Buscar dados (com paralelização)
        try:
            invoices_data = self._fetch_all_invoices_parallel(school)
            cache.set(cache_key, invoices_data, timeout=3600)

            return Response({
                **invoices_data,
                'cached': False,
                'cache_info': 'Dados recém-buscados do SIGA'
            }, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Falha na comunicação com o SIGA: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

    def _fetch_all_invoices_parallel(self, school):
        """Busca boletos em PARALELO (muito mais rápido)"""

        # 1. Buscar alunos
        students = self._fetch_students(school.application_token)

        if not students:
            return {
                'students': [],
                'summary': {
                    'total_students': 0,
                    'total_invoices': 0,
                    'paid_count': 0,
                    'pending_count': 0,
                    'completion_rate': 0,
                },
                'last_updated': timezone.now().isoformat(),
            }

        # 2. Buscar boletos em PARALELO (10 threads simultâneas)
        all_invoices = []
        students_with_invoices = []

        headers = {
            "Authorization": f"Bearer {school.application_token}",
            "Content-Type": "application/json"
        }

        # ✅ PARALELIZAÇÃO: 10 requisições simultâneas
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Criar futures para cada aluno
            future_to_student = {
                executor.submit(
                    self._fetch_student_invoices,
                    student,
                    headers
                ): student
                for student in students
            }

            # Processar resultados conforme completam
            for future in as_completed(future_to_student):
                student = future_to_student[future]
                try:
                    result = future.result()
                    if result:
                        students_with_invoices.append(result['student_data'])
                        all_invoices.extend(result['invoices'])
                except Exception as exc:
                    print(f"Erro ao buscar boletos do aluno {student.get('id')}: {exc}")

        # 3. Calcular estatísticas
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

    def _fetch_student_invoices(self, student, headers):
        """Busca boletos de UM aluno (para execução paralela)"""
        student_id = student.get('id')
        if not student_id:
            return None

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

                    invoice_list = []
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
                        invoice_list.append(invoice_data)

                    return {
                        'student_data': student_invoices,
                        'invoices': invoice_list
                    }

        except requests.exceptions.RequestException:
            pass

        return None

    def _fetch_students(self, token):
        """Busca todos os alunos (mantido igual)"""
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