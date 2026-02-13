# apps/contacts/views/dashboard_views.py
"""
Dashboard de Métricas - Estatísticas Financeiras e Cadastrais

Fornece visão geral sobre:
- Situação de boletos (pagos, pendentes, cancelados)
- Completude de dados cadastrais dos responsáveis
- KPIs gerais da escola
"""

import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from core.permissions import IsSchoolStaff

logger = logging.getLogger(__name__)


class SchoolDashboardView(APIView):
    """
    GET /api/contacts/dashboard/

    Retorna estatísticas gerais da escola:
    - Situação financeira (boletos)
    - Completude cadastral (responsáveis)
    - KPIs gerais

    Permissões: IsSchoolStaff (Manager/Operator)
    """
    permission_classes = [IsSchoolStaff]

    def get(self, request):
        """GET /api/contacts/dashboard/"""

        # Validações
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school

        if not school.application_token:
            return Response(
                {
                    "error": "Escola sem token configurado",
                    "detail": "Configure o application_token no admin"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"📊 Buscando dashboard - Escola: {school.school_name}")

        try:
            # Buscar dados em paralelo
            headers = {
                "Authorization": f"Bearer {school.application_token}",
                "Content-Type": "application/json"
            }

            # 1. Buscar alunos
            students = self._fetch_students(headers)

            if not students:
                return Response({
                    "error": "Nenhum aluno encontrado",
                    "boletos": self._empty_boletos_stats(),
                    "responsaveis": self._empty_guardians_stats(),
                    "alunos": {"total": 0, "com_boletos": 0, "sem_boletos": 0}
                })

            # 2. Buscar boletos e analisar dados em paralelo
            logger.info(f"📊 Analisando {len(students)} alunos...")

            boletos_stats = {
                'total': 0,
                'abertos': 0,
                'pagos': 0,
                'cancelados': 0,
                'vencidos': 0,
                'valor_total': 0.0,
                'valor_recebido': 0.0,
                'valor_pendente': 0.0,
            }

            guardians_stats = {
                'total_alunos': len(students),
                'sem_cpf': 0,
                'sem_email': 0,
                'sem_telefone': 0,
                'sem_dados_completos': 0,
            }

            alunos_com_boletos = 0

            # Processar em paralelo (10 threads)
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(self._process_student, student, headers): student
                    for student in students
                }

                for future in as_completed(futures):
                    try:
                        result = future.result()

                        if result:
                            # Agregar estatísticas de boletos
                            if result['invoices']:
                                alunos_com_boletos += 1

                                for inv in result['invoices']:
                                    boletos_stats['total'] += 1

                                    status_code = inv.get('situacao_titulo', '')
                                    valor_doc = float(inv.get('valor_documento', 0) or 0)
                                    valor_recebido = float(inv.get('valor_recebido_total', 0) or 0)
                                    dt_venc = inv.get('dt_vencimento')

                                    boletos_stats['valor_total'] += valor_doc

                                    if status_code == 'LIQ':  # Liquidado/Pago
                                        boletos_stats['pagos'] += 1
                                        boletos_stats['valor_recebido'] += valor_recebido
                                    elif status_code == 'CAN':  # Cancelado
                                        boletos_stats['cancelados'] += 1
                                    else:  # Aberto
                                        boletos_stats['abertos'] += 1
                                        boletos_stats['valor_pendente'] += valor_doc

                                        # Verificar se está vencido
                                        if dt_venc:
                                            try:
                                                venc = datetime.fromisoformat(dt_venc.replace('Z', '+00:00'))
                                                if venc.date() < timezone.now().date():
                                                    boletos_stats['vencidos'] += 1
                                            except:
                                                pass

                            # Agregar estatísticas cadastrais
                            guardian_data = result.get('guardian_data', {})
                            if guardian_data:
                                if not guardian_data.get('cpf'):
                                    guardians_stats['sem_cpf'] += 1
                                if not guardian_data.get('email'):
                                    guardians_stats['sem_email'] += 1
                                if not guardian_data.get('telefone'):
                                    guardians_stats['sem_telefone'] += 1

                                # Dados incompletos: falta pelo menos 1 campo
                                if not (guardian_data.get('cpf') and
                                        guardian_data.get('email') and
                                        guardian_data.get('telefone')):
                                    guardians_stats['sem_dados_completos'] += 1

                    except Exception as e:
                        logger.error(f"Erro ao processar aluno: {e}")
                        continue

            # 3. Calcular métricas derivadas
            taxa_inadimplencia = 0.0
            if boletos_stats['total'] > 0:
                taxa_inadimplencia = round(
                    (boletos_stats['abertos'] / boletos_stats['total']) * 100,
                    2
                )

            taxa_vencidos = 0.0
            if boletos_stats['abertos'] > 0:
                taxa_vencidos = round(
                    (boletos_stats['vencidos'] / boletos_stats['abertos']) * 100,
                    2
                )

            taxa_completude = 0.0
            if guardians_stats['total_alunos'] > 0:
                completos = guardians_stats['total_alunos'] - guardians_stats['sem_dados_completos']
                taxa_completude = round(
                    (completos / guardians_stats['total_alunos']) * 100,
                    2
                )

            # 4. Montar resposta
            response_data = {
                'boletos': {
                    'total': boletos_stats['total'],
                    'abertos': boletos_stats['abertos'],
                    'pagos': boletos_stats['pagos'],
                    'cancelados': boletos_stats['cancelados'],
                    'vencidos': boletos_stats['vencidos'],
                    'valores': {
                        'total': round(boletos_stats['valor_total'], 2),
                        'recebido': round(boletos_stats['valor_recebido'], 2),
                        'pendente': round(boletos_stats['valor_pendente'], 2),
                    },
                    'taxas': {
                        'inadimplencia': taxa_inadimplencia,
                        'vencidos_sobre_abertos': taxa_vencidos,
                        'pagamento': round((boletos_stats['pagos'] / boletos_stats['total'] * 100), 2) if boletos_stats[
                                                                                                              'total'] > 0 else 0
                    }
                },
                'responsaveis': {
                    'total_alunos': guardians_stats['total_alunos'],
                    'cadastros_incompletos': {
                        'sem_cpf': guardians_stats['sem_cpf'],
                        'sem_email': guardians_stats['sem_email'],
                        'sem_telefone': guardians_stats['sem_telefone'],
                        'total_incompletos': guardians_stats['sem_dados_completos'],
                    },
                    'taxas': {
                        'completude': taxa_completude,
                        'cpf_faltante': round((guardians_stats['sem_cpf'] / guardians_stats['total_alunos'] * 100),
                                              2) if guardians_stats['total_alunos'] > 0 else 0,
                        'email_faltante': round((guardians_stats['sem_email'] / guardians_stats['total_alunos'] * 100),
                                                2) if guardians_stats['total_alunos'] > 0 else 0,
                        'telefone_faltante': round(
                            (guardians_stats['sem_telefone'] / guardians_stats['total_alunos'] * 100), 2) if
                        guardians_stats['total_alunos'] > 0 else 0,
                    }
                },
                'alunos': {
                    'total': len(students),
                    'com_boletos': alunos_com_boletos,
                    'sem_boletos': len(students) - alunos_com_boletos,
                    'taxa_com_boletos': round((alunos_com_boletos / len(students) * 100), 2) if len(students) > 0 else 0
                },
                'metadados': {
                    'escola_id': school.id,
                    'escola_nome': school.school_name,
                    'data_atualizacao': timezone.now().isoformat(),
                    'total_processado': len(students),
                }
            }

            logger.info(f"✓ Dashboard gerado com sucesso")
            return Response(response_data, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na comunicação com SIGA: {e}")
            return Response(
                {"error": f"Erro ao comunicar com SIGA: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Erro inesperado: {e}", exc_info=True)
            return Response(
                {"error": f"Erro inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _fetch_students(self, headers):
        """Busca lista de alunos da API SIGA"""
        url = "https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/"

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

    def _process_student(self, student, headers):
        """Processa um aluno: busca boletos e dados cadastrais"""
        student_id = student.get('id')

        if not student_id:
            return None

        result = {
            'invoices': [],
            'guardian_data': {}
        }

        try:
            # Buscar boletos
            r = requests.get(
                "https://siga.activesoft.com.br/api/v0/informacoes_boleto/",
                headers=headers,
                params={'id_aluno': student_id},
                timeout=10
            )

            if r.status_code == 200:
                data = r.json()
                result['invoices'] = data.get('resultados', [])

                # Extrair dados do responsável (vem no primeiro boleto)
                if result['invoices']:
                    first = result['invoices'][0]
                    # O SIGA geralmente retorna dados do pagador/responsável
                    pagador = first.get('pagador', '')

                    # Tentar extrair CPF do campo pagador (formato: "Nome (CPF: 123.456.789-00)")
                    cpf = None
                    email = None
                    telefone = None

                    if 'CPF' in pagador or 'cpf' in pagador:
                        # Extrair CPF
                        import re
                        cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', pagador)
                        if cpf_match:
                            cpf = cpf_match.group()

                    result['guardian_data'] = {
                        'cpf': cpf,
                        'email': email,  # SIGA não retorna email no boleto
                        'telefone': telefone,  # SIGA não retorna telefone no boleto
                    }
                else:
                    # Sem boletos: considerar dados do próprio aluno
                    result['guardian_data'] = {
                        'cpf': student.get('cpf_responsavel'),  # Se disponível
                        'email': student.get('email_responsavel'),  # Se disponível
                        'telefone': student.get('telefone_responsavel'),  # Se disponível
                    }

            return result

        except Exception as e:
            logger.warning(f"Erro ao processar aluno {student_id}: {e}")
            return None

    def _empty_boletos_stats(self):
        """Retorna estrutura vazia de estatísticas de boletos"""
        return {
            'total': 0,
            'abertos': 0,
            'pagos': 0,
            'cancelados': 0,
            'vencidos': 0,
            'valores': {'total': 0.0, 'recebido': 0.0, 'pendente': 0.0},
            'taxas': {'inadimplencia': 0.0, 'vencidos_sobre_abertos': 0.0, 'pagamento': 0.0}
        }

    def _empty_guardians_stats(self):
        """Retorna estrutura vazia de estatísticas de responsáveis"""
        return {
            'total_alunos': 0,
            'cadastros_incompletos': {
                'sem_cpf': 0,
                'sem_email': 0,
                'sem_telefone': 0,
                'total_incompletos': 0
            },
            'taxas': {
                'completude': 0.0,
                'cpf_faltante': 0.0,
                'email_faltante': 0.0,
                'telefone_faltante': 0.0
            }
        }