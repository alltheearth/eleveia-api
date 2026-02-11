# apps/contacts/views/guardian_views.py

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.core.cache import cache
import requests

from ..serializers.guardian_serializers import GuardianDetailSerializer
from ..services.siga_integration_service import SigaIntegrationService
from ..services.guardian_aggregator_service import GuardianAggregatorService

logger = logging.getLogger(__name__)


class GuardianPagination(PageNumberPagination):
    """Paginação customizada para responsáveis."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class StudentsGuardiansView(APIView):
    """
    API para listar responsáveis (guardians) com seus filhos matriculados.

    Retorna informações completas incluindo:
    - Dados pessoais do responsável
    - Endereço completo
    - Tipo de parentesco
    - Lista de filhos matriculados
    - Documentos anexados

    **Permissões:** Requer autenticação
    **Paginação:** 20 registros por página (configurável via query param)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = GuardianPagination

    @extend_schema(
        summary="Listar responsáveis com filhos",
        description=(
                "Retorna lista paginada de responsáveis com informações completas "
                "incluindo dados pessoais, endereço, parentesco e lista de filhos matriculados."
        ),
        responses={
            200: OpenApiResponse(
                response=GuardianDetailSerializer(many=True),
                description="Lista de responsáveis retornada com sucesso"
            ),
            403: OpenApiResponse(description="Usuário sem permissão"),
            500: OpenApiResponse(description="Erro ao buscar dados da API externa"),
        },
        tags=['Responsáveis']
    )
    def get(self, request, *args, **kwargs):
        """
        GET /api/v1/contacts/guardians/

        Lista todos os responsáveis com seus filhos.
        """
        # ✅ Validações de segurança
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
        search_query = request.query_params.get('search', '').strip()

        # Cache key
        cache_key = f"guardians:school:{school.id}"
        if search_query:
            cache_key += f":search:{search_query}"

        # Tentar buscar do cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {cache_key}")

            # Aplicar paginação
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(cached_data['guardians'], request)

            return paginator.get_paginated_response(page)

        try:
            # Buscar dados do SIGA
            logger.info(f"Fetching data from SIGA for school {school.id}")

            siga_service = SigaIntegrationService(token)
            all_data = siga_service.fetch_all_data()

            # Agregar e enriquecer dados
            aggregator = GuardianAggregatorService()
            guardians_enriched = aggregator.build_guardians_response(
                guardians=all_data['guardians'],
                students_relations=all_data['students_relations'],
                students_academic=all_data['students_academic']
            )

            # Aplicar filtro de busca, se fornecido
            if search_query:
                guardians_enriched = self._filter_by_search(guardians_enriched, search_query)

            # Serializar
            serializer = GuardianDetailSerializer(guardians_enriched, many=True)

            # Cachear por 30 minutos
            cache_data = {'guardians': serializer.data}
            cache.set(cache_key, cache_data, timeout=1800)
            logger.info(f"Cached data for {cache_key}")

            # Aplicar paginação
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(serializer.data, request)

            return paginator.get_paginated_response(page)

        except requests.exceptions.Timeout:
            logger.error("Timeout communicating with SIGA")
            return Response(
                {"error": "O SIGA demorou muito para responder. Tente novamente."},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with SIGA: {str(e)}")
            return Response(
                {"error": f"Falha na comunicação com o SIGA: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except Exception as e:
            logger.exception(f"Unexpected error processing guardians: {str(e)}")
            return Response(
                {"error": "Erro interno ao processar dados"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _filter_by_search(self, guardians: list, search_query: str) -> list:
        """
        Filtra responsáveis por nome (responsável OU filho).

        Args:
            guardians: Lista de responsáveis
            search_query: Termo de busca

        Returns:
            Lista filtrada
        """
        search_lower = search_query.lower()
        filtered = []

        for guardian in guardians:
            # Buscar no nome do responsável
            if search_lower in guardian.get('nome', '').lower():
                filtered.append(guardian)
                continue

            # Buscar no nome dos filhos
            for child in guardian.get('filhos', []):
                if search_lower in child.get('nome', '').lower():
                    filtered.append(guardian)
                    break

        return filtered