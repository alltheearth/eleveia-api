# apps/contacts/views_new.py
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsSchoolStaff


class StudentGuardianView(APIView):
    """Busca responsáveis do aluno no SIGA"""
    permission_classes = [IsSchoolStaff]

    def get(self, request, student_id):
        # ✅ Validação segura
        if not hasattr(request.user, 'profile'):
            return Response(
                {"error": "Usuário sem perfil"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.profile.school:
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school

        if not school.application_token:
            return Response(
                {"error": "Escola sem token configurado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Agora sim, GARANTIDO que tem token
        token = school.application_token

        url = "https://siga.activesoft.com.br/api/v0/lista_responsaveis_dados_sensiveis/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {'aluno_id': student_id}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            return Response(response.json(), status=response.status_code)

        except requests.exceptions.Timeout:
            return Response({"error": "O SIGA demorou muito para responder."}, status=504)
        except requests.exceptions.RequestException:
            return Response({"error": "Falha na comunicação com o SIGA"}, status=502)


class StudentInvoiceView(APIView):
    """Busca boletos do aluno no SIGA"""
    permission_classes = [IsSchoolStaff]

    def get(self, request, student_id):
        # ✅ Validação segura
        if not hasattr(request.user, 'profile'):
            return Response(
                {"error": "Usuário sem perfil"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.profile.school:
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school

        if not school.application_token:
            return Response(
                {"error": "Escola sem token configurado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        token = school.application_token

        url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {'id_aluno': student_id}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            invoices_list = data.get('resultados', [])

            paid_invoices = []
            pending_invoices = []

            for item in invoices_list:
                invoice_data = {
                    "invoice_number": item.get("titulo"),
                    "bank": item.get("nome_banco"),
                    "due_date": item.get("dt_vencimento"),
                    "payment_date": item.get("dt_pagamento"),
                    "total_amount": item.get("valor_documento"),
                    "received_amount": item.get("valor_recebido_total"),
                    "status_code": item.get("situacao_titulo"),
                    "installment": item.get("parcela_cobranca"),
                    "digitable_line": item.get("linha_digitavel"),
                    "payment_url": item.get("link_pagamento"),
                    "student_name": item.get("aluno"),
                    "class_name": item.get("turma"),
                }

                if item.get("situacao_titulo") == "LIQ":
                    paid_invoices.append(invoice_data)
                else:
                    pending_invoices.append(invoice_data)

            first = invoices_list[0] if invoices_list else {}

            return Response({
                "student_info": {
                    "name": first.get("aluno", "N/A"),
                    "class": first.get("turma", "N/A"),
                    "registration": first.get("aluno_matricula", "N/A")
                },
                "summary": {
                    "paid_count": len(paid_invoices),
                    "pending_count": len(pending_invoices)
                },
                "paid_invoices": paid_invoices,
                "pending_invoices": pending_invoices
            })

        except requests.exceptions.RequestException:
            return Response({"error": "Falha na comunicação com o SIGA"}, status=502)