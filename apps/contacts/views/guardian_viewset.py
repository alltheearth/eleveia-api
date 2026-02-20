# apps/contacts/views/guardian_viewset.py

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ViewSet ÚNICO para Guardians (Responsáveis)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUBSTITUI:
- guardian_viewset.py (antigo)
- guardian_unified_view.py
- guardian_views.py
- student_invoice_views.py
- models/guardian_viewset.py (cópia errada)

ROTAS:
- GET    /api/v1/contacts/guardians/                → list()
- GET    /api/v1/contacts/guardians/{id}/           → retrieve()
- GET    /api/v1/contacts/guardians/{id}/invoices/  → invoices()
- GET    /api/v1/contacts/guardians/stats/          → stats()
- POST   /api/v1/contacts/guardians/refresh/        → refresh()

RESPONSABILIDADES:
- Receber HTTP request
- Validar permissões e escola
- Extrair query params
- Chamar services
- Serializar e retornar resposta

NÃO FAZ:
- Lógica de negócio (delega para services)
- Filtros complexos (delega para selectors)
- Cache direto (delega para SigaCacheManager)
- Chamadas HTTP ao SIGA (delega para services)
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from core.permissions import IsSchoolStaff
from core.mixins import SigaIntegrationMixin
from ..services.guardian_service import GuardianService
from ..services.invoice_service import InvoiceService
from ..selectors.guardian_selectors import GuardianSelector
from ..serializers.guardian_serializers import (
    GuardianListSerializer,
    GuardianDetailSerializer,
)
from ..serializers.invoice_serializers import (
    GuardianInvoicesResponseSerializer,
    GuardianStatsSerializer,
)

logger = logging.getLogger(__name__)


# =====================================================================
# PAGINAÇÃO
# =====================================================================

class GuardianPagination(PageNumberPagination):
    """Paginação customizada para guardians."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


# =====================================================================
# VIEWSET
# =====================================================================

class GuardianViewSet(SigaIntegrationMixin, viewsets.ViewSet):
    """
    ViewSet para Guardians (Responsáveis).

    Sistema stateless — dados vêm da API SIGA, não do banco local.
    Usa cache Redis para performance.

    Permissões: IsSchoolStaff (managers e operators).
    """

    permission_classes = [IsSchoolStaff]
    pagination_class = GuardianPagination

    # -----------------------------------------------------------------
    # HELPERS INTERNOS
    # -----------------------------------------------------------------

    def _get_school_and_token(self, request):
        """
        Extrai e valida escola + token do usuário logado.

        Returns:
            tuple: (school, token, error_response)
            Se error_response não for None, retorne-o diretamente.
        """
        school = self.get_user_school()
        is_valid, error_response = self.validate_school_integration(school)

        if not is_valid:
            return None, None, error_response

        return school, school.application_token, None

    def _paginate(self, request, data):
        """
        Aplica paginação a uma lista de dicts.

        Returns:
            Response paginada
        """
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(page)

    # -----------------------------------------------------------------
    # LIST — GET /api/v1/contacts/guardians/
    # -----------------------------------------------------------------

    @extend_schema(
        summary="Lista responsáveis da escola",
        description=(
            "Retorna lista paginada de responsáveis com dados básicos, "
            "filhos (nome + turma), resumo financeiro e resumo de documentos.\n\n"
            "**NÃO inclui boletos individuais** (use retrieve para isso).\n\n"
            "**Cache:** 2 horas para dados SIGA."
        ),
        parameters=[
            OpenApiParameter(
                name='search',
                description='Busca em nome, CPF, email, telefone ou nome do filho',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='cpf',
                description='Filtro exato por CPF',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='status_financeiro',
                description='Filtro por situação financeira',
                required=False,
                type=str,
                enum=['em_dia', 'inadimplente', 'todos'],
            ),
            OpenApiParameter(
                name='docs_completos',
                description='Filtrar por completude de documentos',
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name='ordering',
                description='Ordenação (nome, -nome)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='page',
                description='Número da página',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='page_size',
                description='Itens por página (máx: 50)',
                required=False,
                type=int,
            ),
        ],
        responses={
            200: GuardianListSerializer(many=True),
            403: OpenApiResponse(description="Sem permissão ou sem escola"),
            500: OpenApiResponse(description="Erro na integração SIGA"),
        },
        tags=['Guardians'],
    )
    def list(self, request):
        """
        Lista responsáveis com filtros e paginação.
        Versão leve para renderizar cards — sem boletos individuais.
        """
        # 1. Validar escola
        school, token, error = self._get_school_and_token(request)
        if error:
            return error

        # 2. Extrair query params
        search = request.query_params.get('search', '').strip()
        cpf = request.query_params.get('cpf', '').strip()
        status_financeiro = request.query_params.get('status_financeiro', '').strip()
        docs_completos = request.query_params.get('docs_completos', '').strip()
        ordering = request.query_params.get('ordering', 'nome').strip()

        try:
            # 3. Buscar guardians (com cache via service)
            guardians = GuardianService.get_guardians_list(
                school_id=school.id,
                token=token,
            )

            # 4. Aplicar filtros
            if search:
                guardians = GuardianSelector.filter_by_search(guardians, search)

            if cpf:
                guardians = GuardianSelector.filter_by_cpf(guardians, cpf)

            if status_financeiro and status_financeiro != 'todos':
                guardians = GuardianSelector.filter_by_status_financeiro(
                    guardians, status_financeiro
                )

            if docs_completos:
                is_completo = docs_completos.lower() in ('true', '1', 'sim')
                guardians = GuardianSelector.filter_by_docs_completos(
                    guardians, is_completo
                )

            # 5. Ordenar
            guardians = GuardianSelector.order_by(guardians, ordering)

            # 6. Serializar
            serializer = GuardianListSerializer(guardians, many=True)

            # 7. Paginar e retornar
            return self._paginate(request, serializer.data)

        except Exception as e:
            logger.exception(f"Erro ao listar guardians: {e}")
            return Response(
                {"error": "Erro ao buscar responsáveis. Tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------------------------------------
    # RETRIEVE — GET /api/v1/contacts/guardians/{id}/
    # -----------------------------------------------------------------

    @extend_schema(
        summary="Detalhes completos de um responsável",
        description=(
            "Retorna informações completas incluindo:\n"
            "- Dados pessoais (nome, CPF, RG, nascimento, profissão...)\n"
            "- Endereço completo\n"
            "- Filhos com dados acadêmicos\n"
            "- Boletos de cada filho\n"
            "- Resumos financeiros\n"
            "- Documentos detalhados\n\n"
            "**Cache:** 1 hora para detalhes com boletos."
        ),
        parameters=[
            OpenApiParameter(
                name='ano_letivo',
                description='Filtra boletos por ano de vencimento',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='situacao_boleto',
                description='Filtra boletos por situação',
                required=False,
                type=str,
                enum=['ABE', 'LIQ', 'CAN', 'todos'],
            ),
        ],
        responses={
            200: GuardianDetailSerializer,
            403: OpenApiResponse(description="Sem permissão"),
            404: OpenApiResponse(description="Responsável não encontrado"),
            500: OpenApiResponse(description="Erro na integração SIGA"),
        },
        tags=['Guardians'],
    )
    def retrieve(self, request, pk=None):
        """
        Retorna detalhes completos de um responsável com boletos.
        """
        # 1. Validar escola
        school, token, error = self._get_school_and_token(request)
        if error:
            return error

        # 2. Validar ID
        try:
            guardian_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "ID inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Extrair filtros de boletos
        ano_letivo = request.query_params.get('ano_letivo', '').strip()
        situacao_boleto = request.query_params.get('situacao_boleto', '').strip()

        try:
            # 4. Buscar guardian completo (com boletos)
            guardian = GuardianService.get_guardian_detail(
                guardian_id=guardian_id,
                school_id=school.id,
                token=token,
                ano_letivo=ano_letivo or None,
                situacao_boleto=situacao_boleto or None,
            )

            if not guardian:
                return Response(
                    {"error": "Responsável não encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 5. Serializar e retornar
            serializer = GuardianDetailSerializer(guardian)
            return Response(serializer.data)

        except Exception as e:
            logger.exception(f"Erro ao buscar guardian {pk}: {e}")
            return Response(
                {"error": "Erro ao buscar responsável. Tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------------------------------------
    # INVOICES — GET /api/v1/contacts/guardians/{id}/invoices/
    # -----------------------------------------------------------------

    @extend_schema(
        summary="Boletos de um responsável",
        description=(
            "Retorna apenas dados financeiros (boletos) de um responsável.\n"
            "Sem dados pessoais — só boletos dos filhos.\n\n"
            "Útil para:\n"
            "- Aba financeiro\n"
            "- Filtro por ano\n"
            "- Refresh de boletos sem recarregar tudo"
        ),
        parameters=[
            OpenApiParameter(
                name='ano',
                description='Filtra por ano de vencimento',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='situacao',
                description='Filtra por situação (ABE, LIQ, CAN)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='filho_id',
                description='Filtra boletos de um filho específico',
                required=False,
                type=int,
            ),
        ],
        responses={
            200: GuardianInvoicesResponseSerializer,
            404: OpenApiResponse(description="Responsável não encontrado"),
        },
        tags=['Guardians'],
    )
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """
        Retorna apenas boletos e resumos (sem dados pessoais).
        """
        # 1. Validar escola
        school, token, error = self._get_school_and_token(request)
        if error:
            return error

        # 2. Validar ID
        try:
            guardian_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "ID inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Extrair filtros
        ano = request.query_params.get('ano', '').strip() or None
        situacao = request.query_params.get('situacao', '').strip() or None
        filho_id_raw = request.query_params.get('filho_id', '').strip()
        filho_id = int(filho_id_raw) if filho_id_raw else None

        try:
            # 4. Buscar boletos via service
            invoices_data = InvoiceService.get_guardian_invoices(
                guardian_id=guardian_id,
                school_id=school.id,
                token=token,
                ano=ano,
                situacao=situacao,
                filho_id=filho_id,
            )

            if invoices_data is None:
                return Response(
                    {"error": "Responsável não encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 5. Serializar e retornar
            serializer = GuardianInvoicesResponseSerializer(invoices_data)
            return Response(serializer.data)

        except Exception as e:
            logger.exception(f"Erro ao buscar boletos do guardian {pk}: {e}")
            return Response(
                {"error": "Erro ao buscar boletos. Tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------------------------------------
    # STATS — GET /api/v1/contacts/guardians/stats/
    # -----------------------------------------------------------------

    @extend_schema(
        summary="Estatísticas da escola",
        description=(
            "Retorna KPIs e estatísticas globais:\n"
            "- Total de responsáveis e alunos\n"
            "- Situação financeira (inadimplência, valores)\n"
            "- Completude de documentos\n"
            "- Distribuição de parentesco"
        ),
        responses={200: GuardianStatsSerializer},
        tags=['Guardians'],
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retorna estatísticas globais da escola.
        """
        # 1. Validar escola
        school, token, error = self._get_school_and_token(request)
        if error:
            return error

        try:
            # 2. Buscar stats via service
            stats_data = GuardianService.get_stats(
                school_id=school.id,
                token=token,
            )

            # 3. Serializar e retornar
            serializer = GuardianStatsSerializer(stats_data)
            return Response(serializer.data)

        except Exception as e:
            logger.exception(f"Erro ao buscar estatísticas: {e}")
            return Response(
                {"error": "Erro ao calcular estatísticas. Tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------------------------------------
    # REFRESH — POST /api/v1/contacts/guardians/refresh/
    # -----------------------------------------------------------------

    @extend_schema(
        summary="Forçar atualização de dados",
        description=(
            "Invalida o cache e força re-sincronização com a API SIGA.\n"
            "Use quando os dados estiverem desatualizados.\n\n"
            "**Atenção:** A próxima requisição será mais lenta (sem cache)."
        ),
        responses={
            200: OpenApiResponse(description="Cache invalidado com sucesso"),
        },
        tags=['Guardians'],
    )
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """
        Invalida cache e força re-sincronização com SIGA.
        """
        # 1. Validar escola
        school, token, error = self._get_school_and_token(request)
        if error:
            return error

        try:
            # 2. Invalidar cache via service
            GuardianService.invalidate_cache(school_id=school.id)

            logger.info(f"Cache invalidado para escola {school.id}")

            return Response({
                "message": "Cache invalidado. Os dados serão atualizados na próxima consulta.",
                "school_id": school.id,
            })

        except Exception as e:
            logger.exception(f"Erro ao invalidar cache: {e}")
            return Response(
                {"error": "Erro ao invalidar cache."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )