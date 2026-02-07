# apps/contacts/views_new.py
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsSchoolStaff
from collections import defaultdict


class StudentGuardianView(APIView):
    """Busca e classifica responsáveis com seus alunos do SIGA"""
    permission_classes = [IsSchoolStaff]

    def get(self, request):
        # ✅ Validação de segurança
        if not hasattr(request.user, 'profile'):
            return Response({"error": "Usuário sem perfil"}, status=status.HTTP_403_FORBIDDEN)

        if not request.user.profile.school:
            return Response({"error": "Usuário sem escola vinculada"}, status=status.HTTP_403_FORBIDDEN)

        school = request.user.profile.school

        if not school.application_token:
            return Response({"error": "Escola sem token configurado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token = school.application_token

        try:
            # 🔍 BUSCAR TODOS OS RESPONSÁVEIS
            guardians = self._fetch_all_paginated(
                "https://siga.activesoft.com.br/api/v0/lista_responsaveis_dados_sensiveis/",
                token
            )

            # 🔍 BUSCAR TODOS OS ALUNOS
            students = self._fetch_all_paginated(
                "https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/",
                token
            )

            # 📊 PROCESSAR E RELACIONAR DADOS
            result = self._process_guardians_and_students(guardians, students)

            return Response(result, status=status.HTTP_200_OK)

        except requests.exceptions.Timeout:
            return Response({"error": "O SIGA demorou muito para responder."}, status=504)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Falha na comunicação com o SIGA: {str(e)}"}, status=502)

    def _fetch_all_paginated(self, url, token):
        """Busca todos os resultados paginados de uma API"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        all_results = []
        next_url = url

        while next_url:
            response = requests.get(next_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # ✅ CORREÇÃO: Verifica se é lista ou objeto paginado
            if isinstance(data, list):
                # Se retornou uma lista direta, adiciona tudo e para
                all_results.extend(data)
                break
            elif isinstance(data, dict):
                # Se retornou objeto paginado, extrai 'results'
                all_results.extend(data.get('results', []))
                next_url = data.get('next')
            else:
                # Caso inesperado
                break

        return all_results

    def _process_guardians_and_students(self, guardians, students):
        """Processa e relaciona responsáveis com alunos"""

        # Criar índice de responsáveis por ID
        guardians_dict = {g['id']: g for g in guardians}

        # Dicionário para agrupar alunos por responsável
        guardian_students_map = defaultdict(lambda: {
            'as_mother': [],
            'as_father': [],
            'as_primary_guardian': [],
            'as_secondary_guardian': [],
            'as_financial_responsible': []
        })

        # Processar cada aluno e mapear seus responsáveis
        for student in students:
            student_info = {
                'id': student.get('id'),
                'matricula': student.get('matricula'),
                'nome': student.get('nome'),
                'cpf': student.get('cpf'),
                'data_nascimento': student.get('data_nascimento'),
                'celular': student.get('celular'),
                'email': student.get('email')
            }

            # Mãe
            if student.get('mae_id'):
                guardian_students_map[student['mae_id']]['as_mother'].append(student_info)

            # Pai
            if student.get('pai_id'):
                guardian_students_map[student['pai_id']]['as_father'].append(student_info)

            # Responsável principal
            if student.get('responsavel_id'):
                guardian_students_map[student['responsavel_id']]['as_primary_guardian'].append(student_info)

            # Responsável secundário
            if student.get('responsavel_secundario_id'):
                guardian_students_map[student['responsavel_secundario_id']]['as_secondary_guardian'].append(
                    student_info)

            # Responsável financeiro (assumindo que é o responsável principal)
            # Se houver um campo específico, ajuste aqui
            if student.get('responsavel_id'):
                guardian_students_map[student['responsavel_id']]['as_financial_responsible'].append(student_info)

        # Construir resultado final
        result = {
            'total_guardians': len(guardians),
            'total_students': len(students),
            'guardians_with_missing_data': {
                'missing_cpf': [],
                'missing_email': [],
                'missing_phone': [],
                'missing_multiple': []
            },
            'guardians': []
        }

        for guardian in guardians:
            guardian_id = guardian['id']

            # Verificar dados faltantes
            missing_fields = []
            if not guardian.get('cpf_cnpj'):
                missing_fields.append('cpf_cnpj')
            if not guardian.get('email'):
                missing_fields.append('email')
            if not guardian.get('celular'):
                missing_fields.append('celular')

            # Formatar telefone
            phone = self._format_phone(guardian.get('celular'))

            # Obter relacionamentos
            relationships = guardian_students_map.get(guardian_id, {
                'as_mother': [],
                'as_father': [],
                'as_primary_guardian': [],
                'as_secondary_guardian': [],
                'as_financial_responsible': []
            })

            # Determinar tipos de relacionamento
            relationship_types = []
            if relationships['as_mother']:
                relationship_types.append('mãe')
            if relationships['as_father']:
                relationship_types.append('pai')
            if relationships['as_primary_guardian']:
                relationship_types.append('responsável_principal')
            if relationships['as_secondary_guardian']:
                relationship_types.append('responsável_secundário')
            if relationships['as_financial_responsible']:
                relationship_types.append('responsável_financeiro')

            # Contar total de alunos (sem duplicação)
            all_student_ids = set()
            for rel_type in relationships.values():
                all_student_ids.update([s['id'] for s in rel_type])

            guardian_data = {
                'id': guardian_id,
                'nome': guardian.get('nome'),
                'cpf_cnpj': guardian.get('cpf_cnpj'),
                'email': guardian.get('email'),
                'celular': guardian.get('celular'),
                'celular_formatado': phone,
                'sexo': guardian.get('sexo'),
                'data_nascimento': guardian.get('data_nascimento'),
                'logradouro': guardian.get('logradouro'),
                'bairro': guardian.get('bairro'),
                'cidade': guardian.get('cidade'),
                'uf': guardian.get('uf'),
                'cep': guardian.get('cep'),
                'profissao_nome': guardian.get('profissao_nome'),
                'missing_data': missing_fields,
                'has_missing_data': len(missing_fields) > 0,
                'relationship_types': relationship_types,
                'total_students': len(all_student_ids),
                'students': {
                    'as_mother': relationships['as_mother'],
                    'as_father': relationships['as_father'],
                    'as_primary_guardian': relationships['as_primary_guardian'],
                    'as_secondary_guardian': relationships['as_secondary_guardian'],
                    'as_financial_responsible': relationships['as_financial_responsible']
                }
            }

            result['guardians'].append(guardian_data)

            # Adicionar aos grupos de dados faltantes
            if missing_fields:
                if 'cpf_cnpj' in missing_fields:
                    result['guardians_with_missing_data']['missing_cpf'].append(guardian_data['nome'])
                if 'email' in missing_fields:
                    result['guardians_with_missing_data']['missing_email'].append(guardian_data['nome'])
                if 'celular' in missing_fields:
                    result['guardians_with_missing_data']['missing_phone'].append(guardian_data['nome'])
                if len(missing_fields) > 1:
                    result['guardians_with_missing_data']['missing_multiple'].append({
                        'nome': guardian_data['nome'],
                        'missing': missing_fields
                    })

        # Estatísticas adicionais
        result['statistics'] = {
            'total_with_missing_data': len([g for g in result['guardians'] if g['has_missing_data']]),
            'total_missing_cpf': len(result['guardians_with_missing_data']['missing_cpf']),
            'total_missing_email': len(result['guardians_with_missing_data']['missing_email']),
            'total_missing_phone': len(result['guardians_with_missing_data']['missing_phone']),
            'total_missing_multiple': len(result['guardians_with_missing_data']['missing_multiple']),
            'guardians_as_mother': len([g for g in result['guardians'] if 'mãe' in g['relationship_types']]),
            'guardians_as_father': len([g for g in result['guardians'] if 'pai' in g['relationship_types']]),
            'guardians_as_primary': len(
                [g for g in result['guardians'] if 'responsável_principal' in g['relationship_types']]),
            'guardians_as_secondary': len(
                [g for g in result['guardians'] if 'responsável_secundário' in g['relationship_types']]),
        }

        return result

    def _format_phone(self, phone):
        """Formata telefone para o padrão 55DDXXXXXXXXX"""
        if not phone:
            return None

        # Remove todos os caracteres não numéricos
        numero = ''.join(filter(str.isdigit, phone))

        if not numero:
            return None

        # Remove 55 se já existir
        if numero.startswith('55'):
            numero = numero[2:]

        # Adiciona 55
        return f"55{numero}"


class StudentInvoiceView(APIView):
    """Busca boletos do aluno no SIGA"""
    permission_classes = [IsSchoolStaff]

    def get(self, request):
        student_id = request.query_params.get('student_id')

        if not student_id:
            return Response(
                {"error": "student_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

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