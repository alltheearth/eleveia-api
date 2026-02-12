# apps/contacts/views/guardian_viewset.py
"""
ViewSet para Guardians (Responsáveis) - VERSÃO CORRIGIDA

IMPORTANTE: Este ViewSet NÃO usa QuerySet (sistema stateless).
Dados vêm direto da API SIGA via services.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.permissions import IsSchoolStaff
from ..services.guardian_service import GuardianService
from ..selectors.guardian_selectors import GuardianSelector
from ..serializers.guardian_list_serializer import GuardianListSerializer
from ..serializers.guardian_serializers import GuardianDetailSerializer

logger = logging.getLogger(__name__)


class GuardianPagination(PageNumberPagination):
    """Paginação customizada para guardians."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class GuardianViewSet(viewsets.ViewSet):
    """
    ViewSet para gerenciamento de Guardians (Responsáveis).

    ⚠️ STATELESS: Não usa QuerySet/Database.
    Dados vêm direto da API SIGA.

    Endpoints:
    - list: Lista guardians com paginação
    - retrieve: Detalhes completos de um guardian (com boletos)
    - invoices: Apenas boletos de um guardian
    """

    permission_classes = [IsSchoolStaff]
    pagination_class = GuardianPagination

    def get_serializer_class(self):
        """Retorna serializer apropriado por action."""
        if self.action == 'list':
            return GuardianListSerializer
        return GuardianDetailSerializer

    def get_serializer(self, *args, **kwargs):
        """Instancia serializer."""
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """Context para serializers."""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    @extend_schema(
        summary="Lista guardians da escola",
        description=(
                "Retorna lista paginada de guardians (responsáveis) vinculados à escola. "
                "Versão leve sem boletos para performance."
        ),
        parameters=[
            OpenApiParameter(
                name='search',
                description='Busca por nome, CPF ou nome do filho',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='cpf',
                description='Filtro exato por CPF',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Ordenação (nome, -nome)',
                required=False,
                type=str
            ),
        ],
        tags=['Guardians']
    )
    def list(self, request):
        """
        GET /api/v1/contacts/guardians/

        Lista guardians com filtros e paginação.

        Query params:
        - search: Busca em nome, CPF, email
        - cpf: Filtro exato por CPF
        - ordering: nome ou -nome
        - page: Número da página
        - page_size: Itens por página (max: 100)
        """
        # 1. Validações
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school
        token = school.application_token

        if not token:
            return Response(
                {"error": "Escola sem token configurado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2. Extrai query params
        search = request.query_params.get('search', '').strip()
        cpf = request.query_params.get('cpf', '').strip()
        ordering = request.query_params.get('ordering', 'nome')

        try:
            # 3. Busca guardians (com cache)
            guardians = GuardianService.get_guardians_list(
                school_id=school.id,
                token=token
            )

            # 4. Aplica filtros
            if search:
                guardians = GuardianSelector.filter_by_search(guardians, search)

            if cpf:
                guardians = GuardianSelector.filter_by_cpf(guardians, cpf)

            # 5. Ordena
            guardians = GuardianSelector.order_by(guardians, ordering)

            # 6. Pagina
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(guardians, request)

            # 7. Serializa
            serializer = self.get_serializer(page, many=True)

            # 8. Retorna paginado
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.exception(f"Error listing guardians: {e}")
            return Response(
                {"error": "Erro ao buscar guardians", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Detalhes completos de um guardian",
        description=(
                "Retorna informações completas de um guardian incluindo:\n"
                "- Dados pessoais completos\n"
                "- Endereço\n"
                "- Lista de filhos com dados acadêmicos\n"
                "- Boletos de cada filho\n"
                "- Resumos financeiros"
        ),
        tags=['Guardians']
    )
    def retrieve(self, request, pk=None):
        """
        GET /api/v1/contacts/guardians/{id}/

        Retorna detalhes completos de um guardian (com boletos).
        """
        # 1. Validações
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school
        token = school.application_token

        if not token:
            return Response(
                {"error": "Escola sem token configurado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            guardian_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "ID inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2. Busca guardian com boletos
            guardian = GuardianService.get_guardian_detail(
                guardian_id=guardian_id,
                school_id=school.id,
                token=token,
                include_invoices=True
            )

            # 3. Verifica se encontrou
            if not guardian:
                return Response(
                    {"error": "Guardian não encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 4. Serializa
            serializer = self.get_serializer(guardian)

            # 5. Retorna
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error retrieving guardian {pk}: {e}")
            return Response(
                {"error": "Erro ao buscar guardian", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Resumo de boletos de um guardian",
        description="Retorna apenas informações financeiras (boletos) de um guardian",
        tags=['Guardians']
    )
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """
        GET /api/v1/contacts/guardians/{id}/invoices/

        Retorna apenas boletos e resumos (sem dados pessoais).
        """
        # 1. Busca guardian completo
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response(
                {"error": "Usuário sem escola vinculada"},
                status=status.HTTP_403_FORBIDDEN
            )

        school = request.user.profile.school
        token = school.application_token

        if not token:
            return Response(
                {"error": "Escola sem token configurado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            guardian_id = int(pk)

            guardian = GuardianService.get_guardian_detail(
                guardian_id=guardian_id,
                school_id=school.id,
                token=token,
                include_invoices=True
            )

            if not guardian:
                return Response(
                    {"error": "Guardian não encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 2. Extrai apenas dados financeiros
            result = {
                'guardian_id': guardian['id'],
                'guardian_name': guardian['nome'],
                'total_filhos': len(guardian.get('filhos', [])),
                'resumo_geral': guardian.get('resumo_geral_boletos', {}),
                'filhos': [
                    {
                        'id': filho['id'],
                        'nome': filho['nome'],
                        'boletos': filho.get('boletos', []),
                        'resumo': filho.get('resumo_boletos', {})
                    }
                    for filho in guardian.get('filhos', [])
                ]
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error getting invoices for guardian {pk}: {e}")
            return Response(
                {"error": "Erro ao buscar boletos", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )