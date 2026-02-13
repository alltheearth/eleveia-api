# apps/contacts/views/student_invoice_views.py
# VERSÃO CORRIGIDA - Funciona SEM Redis (usa cache local como fallback)

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.utils import timezone
from core.permissions import IsSchoolStaff

logger = logging.getLogger(__name__)

# ========================================
# CACHE LOCAL (fallback quando Redis não está disponível)
# ========================================
_local_cache = {}
_local_cache_timeout = {}


def get_from_cache(key):
    """Tenta pegar do Redis, se falhar usa cache local"""
    try:
        # Tentar Redis primeiro
        data = cache.get(key)
        if data:
            logger.info(f"✓ Dados recuperados do Redis cache")
            return data
    except Exception as e:
        logger.warning(f"Redis indisponível: {str(e)[:100]}")

    # Fallback: cache local
    if key in _local_cache:
        if key in _local_cache_timeout:
            if timezone.now() < _local_cache_timeout[key]:
                logger.info(f"✓ Dados recuperados do cache local (fallback)")
                return _local_cache[key]
            else:
                # Expirou
                del _local_cache[key]
                del _local_cache_timeout[key]

    return None


def set_in_cache(key, value, timeout=3600):
    """Tenta salvar no Redis, se falhar usa cache local"""
    try:
        # Tentar Redis primeiro
        cache.set(key, value, timeout=timeout)
        logger.info(f"💾 Dados salvos no Redis cache")
    except Exception as e:
        logger.warning(f"Redis indisponível, usando cache local: {str(e)[:100]}")
        # Fallback: cache local
        _local_cache[key] = value
        _local_cache_timeout[key] = timezone.now() + timedelta(seconds=timeout)
        logger.info(f"💾 Dados salvos no cache local (fallback por {timeout}s)")


class StudentInvoiceView(APIView):
    """
    Busca TODOS os boletos de TODOS os alunos da escola

    CORREÇÕES APLICADAS:
    - ✅ Sempre retorna dados do aluno (mesmo sem boletos)
    - ✅ Funciona SEM Redis (usa cache local como fallback)
    - ✅ Logging detalhado para debug
    - ✅ Melhor tratamento de erros
    - ✅ Validações robustas
    """
    permission_classes = [IsSchoolStaff]

    def get(self, request):
        """GET /api/contacts/students/invoices/"""

        # ========================================
        # 1. VALIDAÇÕES INICIAIS
        # ========================================
        if not hasattr(request.user, 'profile'):
            logger.error(f"Usuário {request.user.username} sem perfil")
            return Response(
                {"error": "Usuário sem perfil"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.profile.school:
            logger.error(f"Usuário {request.user.username} sem escola vinculada")
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school

        if not school.application_token:
            logger.error(f"Escola {school.id} ({school.school_name}) sem token configurado")
            return Response(
                {
                    "error": "Escola sem token configurado",
                    "detail": "Configure o application_token no admin para integrar com o SIGA"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"📊 Iniciando busca de boletos - Escola: {school.school_name} (ID: {school.id})")

        # ========================================
        # 2. VERIFICAR CACHE (com fallback local)
        # ========================================
        cache_key = f"all_invoices_school_{school.id}"
        cached_data = get_from_cache(cache_key)

        if cached_data:
            logger.info(f"✓ Retornando dados do cache")
            return Response({
                **cached_data,
                'cached': True,
                'cache_info': 'Dados do cache (atualizados a cada 1 hora)',
                'cache_key': cache_key
            }, status=status.HTTP_200_OK)

        # ========================================
        # 3. BUSCAR DADOS DA API SIGA
        # ========================================
        try:
            logger.info(f"🔄 Buscando dados do SIGA (pode demorar alguns segundos)...")
            invoices_data = self._fetch_all_invoices_parallel(school)

            # Log de estatísticas
            logger.info(f"✓ Busca concluída:")
            logger.info(f"  - Alunos encontrados: {invoices_data['summary']['total_students']}")
            logger.info(f"  - Boletos encontrados: {invoices_data['summary']['total_invoices']}")
            logger.info(f"  - Pagos: {invoices_data['summary']['paid_count']}")
            logger.info(f"  - Pendentes: {invoices_data['summary']['pending_count']}")

            # Salvar no cache (com fallback)
            set_in_cache(cache_key, invoices_data, timeout=3600)  # 1 hora

            return Response({
                **invoices_data,
                'cached': False,
                'cache_info': 'Dados recém-buscados do SIGA',
                'cache_key': cache_key
            }, status=status.HTTP_200_OK)

        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout na comunicação com SIGA")
            return Response(
                {
                    "error": "Timeout na comunicação com o SIGA",
                    "detail": "O servidor SIGA demorou muito para responder. Tente novamente."
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.exceptions.ConnectionError:
            logger.error("🔌 Erro de conexão com SIGA")
            return Response(
                {
                    "error": "Erro de conexão com o SIGA",
                    "detail": "Não foi possível conectar ao servidor SIGA. Verifique sua conexão."
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Erro HTTP do SIGA: {e}")
            return Response(
                {
                    "error": f"Erro na comunicação com o SIGA: HTTP {e.response.status_code}",
                    "detail": "O servidor SIGA retornou um erro. Verifique o token de autenticação."
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        except Exception as e:
            logger.error(f"💥 Erro inesperado ao buscar boletos: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": f"Erro inesperado: {str(e)}",
                    "detail": "Ocorreu um erro inesperado. Contate o suporte."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _fetch_all_invoices_parallel(self, school):
        """
        Busca boletos em PARALELO (muito mais rápido)

        CORREÇÃO: Sempre retorna dados do aluno, mesmo sem boletos
        """

        # ========================================
        # 1. BUSCAR ALUNOS
        # ========================================
        logger.info(f"📚 Buscando lista de alunos...")
        students = self._fetch_students(school.application_token)
        logger.info(f"✓ {len(students)} alunos encontrados")

        if not students:
            logger.warning("⚠️ Nenhum aluno encontrado na API SIGA")
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
                'warning': 'Nenhum aluno encontrado na API SIGA'
            }

        # ========================================
        # 2. BUSCAR BOLETOS EM PARALELO
        # ========================================
        logger.info(f"💰 Buscando boletos de {len(students)} alunos (paralelizado em 10 threads)...")

        all_invoices = []
        students_with_data = []
        error_count = 0

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
            for idx, future in enumerate(as_completed(future_to_student), 1):
                student = future_to_student[future]

                # Log de progresso a cada 50 alunos
                if idx % 50 == 0:
                    logger.info(f"  Progresso: {idx}/{len(students)} alunos processados...")

                try:
                    result = future.result()

                    # ✅ CORREÇÃO: Sempre adiciona o aluno (mesmo sem boletos)
                    if result:
                        students_with_data.append(result['student_data'])
                        all_invoices.extend(result['invoices'])
                    else:
                        error_count += 1

                except Exception as exc:
                    error_count += 1
                    student_id = student.get('id', 'N/A')
                    student_name = student.get('nome', 'N/A')
                    logger.error(f"❌ Erro ao buscar boletos do aluno {student_id} ({student_name}): {exc}")

        # Log de erros
        if error_count > 0:
            logger.warning(f"⚠️ {error_count} alunos com erro ao buscar boletos")

        # ========================================
        # 3. CALCULAR ESTATÍSTICAS
        # ========================================
        total_invoices = len(all_invoices)
        paid = sum(1 for inv in all_invoices if inv.get('status_code') == 'LIQ')
        pending = total_invoices - paid

        logger.info(f"✓ Estatísticas calculadas: {total_invoices} boletos ({paid} pagos, {pending} pendentes)")

        return {
            'students': students_with_data,
            'summary': {
                'total_students': len(students_with_data),
                'total_students_from_api': len(students),
                'total_invoices': total_invoices,
                'paid_count': paid,
                'pending_count': pending,
                'completion_rate': round((paid / total_invoices * 100), 2) if total_invoices > 0 else 0,
                'errors': error_count,
            },
            'last_updated': timezone.now().isoformat(),
        }

    def _fetch_student_invoices(self, student, headers):
        """
        Busca boletos de UM aluno (para execução paralela)

        CORREÇÃO: SEMPRE retorna dados do aluno, mesmo sem boletos ou com erro
        """
        student_id = student.get('id')
        student_name = student.get('nome', 'N/A')
        student_registration = student.get('matricula', 'N/A')

        if not student_id:
            logger.warning(f"⚠️ Aluno sem ID: {student_name}")
            return None

        try:
            url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
            params = {'id_aluno': student_id}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()  # Levanta exceção se status != 200

            data = response.json()
            invoices = data.get('resultados', [])

            # ✅ SEMPRE cria estrutura do aluno (mesmo sem boletos)
            student_invoices = {
                'student_id': student_id,
                'student_name': student_name,
                'student_registration': student_registration,
                'student_class': invoices[0].get('turma') if invoices else None,
                'invoices': [],
                'has_invoices': len(invoices) > 0,
                'total_invoices': len(invoices)
            }

            invoice_list = []

            # Processar boletos (se existirem)
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

        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout ao buscar boletos do aluno {student_id} ({student_name})")
            # ✅ Retorna estrutura vazia em caso de timeout
            return {
                'student_data': {
                    'student_id': student_id,
                    'student_name': student_name,
                    'student_registration': student_registration,
                    'student_class': None,
                    'invoices': [],
                    'has_invoices': False,
                    'total_invoices': 0,
                    'error': 'Timeout'
                },
                'invoices': []
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ Erro ao buscar boletos do aluno {student_id} ({student_name}): {str(e)}")
            # ✅ Retorna estrutura vazia em caso de erro
            return {
                'student_data': {
                    'student_id': student_id,
                    'student_name': student_name,
                    'student_registration': student_registration,
                    'student_class': None,
                    'invoices': [],
                    'has_invoices': False,
                    'total_invoices': 0,
                    'error': str(e)
                },
                'invoices': []
            }

        except Exception as e:
            logger.error(f"💥 Erro inesperado ao buscar boletos do aluno {student_id}: {str(e)}")
            # ✅ Retorna estrutura vazia em caso de erro inesperado
            return {
                'student_data': {
                    'student_id': student_id,
                    'student_name': student_name,
                    'student_registration': student_registration,
                    'student_class': None,
                    'invoices': [],
                    'has_invoices': False,
                    'total_invoices': 0,
                    'error': 'Erro inesperado'
                },
                'invoices': []
            }

    def _fetch_students(self, token):
        """
        Busca todos os alunos da API SIGA

        Mantém paginação e tratamento de diferentes formatos de resposta
        """
        url = "https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        all_students = []
        next_url = url

        try:
            while next_url:
                response = requests.get(next_url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                # Formato 1: Lista direta
                if isinstance(data, list):
                    all_students.extend(data)
                    break

                # Formato 2: Objeto com paginação
                elif isinstance(data, dict):
                    all_students.extend(data.get('results', []))
                    next_url = data.get('next')
                else:
                    logger.error(f"Formato de resposta inesperado da API SIGA: {type(data)}")
                    break

            logger.info(f"✓ {len(all_students)} alunos recuperados da API SIGA")
            return all_students

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar lista de alunos: {str(e)}")
            raise