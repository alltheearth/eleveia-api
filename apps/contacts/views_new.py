import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from ..schools.models import School

from core.mixins import SchoolIsolationMixin

class StudentGuardianView(APIView):
    def get(self, request, student_id):
        try:
            # Recomendo usar .filter().first() ou tratar a busca dinamicamente
            escola = School.objects.get(id=SchoolIsolationMixin.get_queryset())
            token = escola.application_token
        except School.DoesNotExist:
            return Response({"error": "Escola não encontrada no banco."}, status=404)

        # 2. Configura a URL com o filtro do aluno
        # Verifique na documentação do SIGA se o parâmetro é 'aluno_id', 'student_id', etc.
        url = "https://siga.activesoft.com.br/api/v0/lista_responsaveis_dados_sensiveis/"
        params = {'aluno_id': student_id}  # Exemplo de parâmetro

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            # Passamos os 'params' para o requests montar a URL final corretamente
            response = requests.get(url, headers=headers, params=params, timeout=10)

            # Se o SIGA retornar erro (ex: 401), o DRF repassa o status corretamente
            return Response(response.json(), status=response.status_code)

        except requests.exceptions.Timeout:
            return Response({"error": "O SIGA demorou muito para responder."}, status=504)
        except requests.exceptions.RequestException:
            return Response({"error": "Falha na comunicação com o SIGA"}, status=502)


class StudentInvoiceView(APIView):
    """
    Retrieves and formats student invoices from SIGA by student_id.
    """

    def get(self, request, student_id):
        # 1. Busca a Escola e o Token
        try:
            school = School.objects.get(id=2)
            token = school.application_token
        except School.DoesNotExist:
            return Response({"error": "School not found in database."}, status=404)


        # 2. Prepara a chamada para o SIGA
        url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {'id_aluno': student_id}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()

            # ✅ ACESSO CORRETO: A lista está dentro de 'resultados'
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

                # Separação por Status
                if item.get("situacao_titulo") == "LIQ":
                    paid_invoices.append(invoice_data)
                else:
                    pending_invoices.append(invoice_data)

            # Pega dados do aluno do primeiro item da lista de resultados
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
            return Response({"error": "SIGA connection failed"}, status=502)
