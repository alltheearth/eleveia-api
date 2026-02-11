# apps/contacts/views/student_guardian_views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import requests

from core.permissions import IsSchoolStaff
from ..services.siga_integration_service import SigaIntegrationService
from ..services.guardian_aggregator_service import GuardianAggregatorService
from ..serializers.guardian_serializers import GuardianDetailSerializer

logger = logging.getLogger(__name__)


class StudentGuardianView(APIView):
    """
    Busca e classifica responsáveis com seus alunos do SIGA.

    Combina dados de 3 APIs:
    - /lista_responsaveis_dados_sensiveis/ (dados pessoais)
    - /lista_alunos_dados_sensiveis/ (vínculos familiares)
    - /acesso/alunos/ (dados acadêmicos)

    Suporta filtro por nome: ?search=Maria
    Cache: 30 minutos
    """
    permission_classes = [IsSchoolStaff]

    def get(self, request):
        """
        GET /api/v1/contacts/students/guardians/

        Query params:
            - search (opcional): Filtra por nome do responsável ou filho

        Returns:
            200: Lista de responsáveis com filhos
            403: Usuário sem permissão
            500: Erro na integração com SIGA
            504: Timeout na comunicação com SIGA
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

        # Cache key (diferente por escola e search)
        cache_key = f"guardians:school:{school.id}"
        if search_query:
            cache_key += f":search:{search_query}"

        # Tentar buscar do cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

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

            # Preparar resposta
            result = {
                'total_guardians': len(guardians_enriched),
                'guardians': serializer.data
            }

            # Cachear por 30 minutos
            cache.set(cache_key, result, timeout=1800)
            logger.info(f"Cached data for {cache_key}")

            return Response(result, status=status.HTTP_200_OK)

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

