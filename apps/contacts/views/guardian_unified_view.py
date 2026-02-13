# apps/contacts/views/guardian_unified_view.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample
)
import requests

from core.permissions import IsSchoolStaff
from ..services.siga_integration_service import SigaIntegrationService
from ..services.guardian_aggregator_service import GuardianAggregatorService
from ..services.guardian_enrichment_service import GuardianEnrichmentService
from ..serializers.guardian_unified_serializer import GuardianUnifiedSerializer
from ..utils.guardian_filters import GuardianFilterService

logger = logging.getLogger(__name__)


class GuardianPagination(PageNumberPagination):
    """
    Paginação customizada para responsáveis.

    Configuração:
    - 20 registros por página (padrão)
    - Até 100 registros por página (máximo)
    - Query param: ?page_size=50
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class GuardianUnifiedView(APIView):
    """
    ✨ API CONSOLIDADA - Responsáveis + Filhos + Boletos + Filtros

    **Features:**
    - Lista responsáveis com filhos e boletos integrados
    - Filtros avançados (nome, email, CPF, telefone, situação)
    - Ordenação alfabética automática (A-Z por nome)
    - Cache inteligente (1-2 horas)
    - Paginação (20 registros por página)
    - Paralelização de boletos (10 threads simultâneas)

    **Performance:**
    - Primeira chamada: ~5-10s (busca SIGA + enriquecimento)
    - Chamadas subsequentes: ~50ms (cache Redis)
    - Cache: 7200s (2 horas)

    **Dados Retornados:**
    ```json
    {
      "count": 150,
      "next": "...",
      "previous": null,
      "results": [
        {
          "id": 1,
          "nome": "Ana Maria Silva",
          "cpf": "123.456.789-00",
          "email": "ana@email.com",
          "telefone": "(11) 98765-4321",
          "endereco": {...},
          "parentesco": "MAE",
          "situacao": {
            "tem_boleto_aberto": true,
            "tem_doc_faltando": false,
            "total_boletos_abertos": 3,
            "valor_total_aberto": "3600.00"
          },
          "filhos": [
            {
              "id": 101,
              "nome": "João Silva",
              "turma": "3º Ano A",
              "boletos": [...],
              "documentos_faltantes": []
            }
          ],
          "documentos": {
            "responsavel": [...],
            "aluno": []
          }
        }
      ]
    }
    ```
    """

    permission_classes = [IsAuthenticated, IsSchoolStaff]
    pagination_class = GuardianPagination

    @extend_schema(
        summary="Listar responsáveis com filhos e boletos",
        description=(
                "Retorna lista paginada de responsáveis com informações completas:\n\n"
                "- Dados pessoais (nome, CPF, email, telefone)\n"
                "- Endereço completo\n"
                "- Situação agregada (boletos abertos, docs faltando)\n"
                "- Lista de filhos com boletos integrados\n"
                "- Documentos (responsável + alunos)\n\n"
                "**Cache:** 2 horas\n"
                "**Ordenação:** Alfabética por nome (A-Z)\n"
                "**Paginação:** 20 registros por página"
        ),
        parameters=[
            OpenApiParameter(
                name='search',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Busca por nome (responsável ou filho), CPF, email ou telefone',
                required=False,
                examples=[
                    OpenApiExample(
                        'Busca por nome',
                        value='Maria Silva'
                    ),
                    OpenApiExample(
                        'Busca por CPF',
                        value='12345678900'
                    )
                ]
            ),
            OpenApiParameter(
                name='email',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filtrar por email exato do responsável',
                required=False,
                examples=[
                    OpenApiExample(
                        'Email',
                        value='maria@example.com'
                    )
                ]
            ),
            OpenApiParameter(
                name='cpf',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filtrar por CPF do responsável (com ou sem formatação)',
                required=False,
                examples=[
                    OpenApiExample(
                        'CPF com formatação',
                        value='123.456.789-00'
                    ),
                    OpenApiExample(
                        'CPF sem formatação',
                        value='12345678900'
                    )
                ]
            ),
            OpenApiParameter(
                name='telefone',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filtrar por telefone do responsável (com ou sem formatação)',
                required=False,
                examples=[
                    OpenApiExample(
                        'Telefone formatado',
                        value='(11) 98765-4321'
                    ),
                    OpenApiExample(
                        'Telefone sem formatação',
                        value='11987654321'
                    )
                ]
            ),
            OpenApiParameter(
                name='tem_boleto_aberto',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Filtrar por responsáveis com boletos abertos (status ABE)',
                required=False,
                examples=[
                    OpenApiExample(
                        'Com boletos abertos',
                        value=True
                    ),
                    OpenApiExample(
                        'Sem boletos abertos',
                        value=False
                    )
                ]
            ),
            OpenApiParameter(
                name='tem_doc_faltando',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Filtrar por responsáveis com documentos faltantes',
                required=False,
                examples=[
                    OpenApiExample(
                        'Com docs faltando',
                        value=True
                    ),
                    OpenApiExample(
                        'Sem docs faltando',
                        value=False
                    )
                ]
            ),
            OpenApiParameter(
                name='page',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Número da página',
                required=False,
                examples=[
                    OpenApiExample('Primeira página', value=1),
                    OpenApiExample('Segunda página', value=2)
                ]
            ),
            OpenApiParameter(
                name='page_size',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Registros por página (máx: 100)',
                required=False,
                examples=[
                    OpenApiExample('20 registros', value=20),
                    OpenApiExample('50 registros', value=50)
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                response=GuardianUnifiedSerializer(many=True),
                description="Lista de responsáveis retornada com sucesso"
            ),
            403: OpenApiResponse(description="Usuário sem permissão"),
            500: OpenApiResponse(description="Erro ao buscar dados da API externa"),
            504: OpenApiResponse(description="Timeout ao comunicar com SIGA")
        },
        tags=['Responsáveis']
    )
    def get(self, request, *args, **kwargs):
        """
        GET /api/v1/contacts/guardians/

        Lista todos os responsáveis com filhos e boletos.
        Suporta filtros avançados e paginação.
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

        # Extrair filtros da query string
        filters = self._extract_filters(request)

        # Cache key (baseado em escola + filtros)
        cache_key = self._generate_cache_key(school.id, filters)

        # Tentar buscar do cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {cache_key}")

            # Aplicar paginação
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(cached_data, request)

            return paginator.get_paginated_response(page)

        try:
            # 1. Buscar dados do SIGA (guardians, students, academic)
            logger.info(f"Fetching data from SIGA for school {school.id}")

            siga_service = SigaIntegrationService(token)
            all_data = siga_service.fetch_all_data()

            # 2. Agregar responsáveis com filhos
            logger.info("Aggregating guardians with students")

            aggregator = GuardianAggregatorService()
            guardians_aggregated = aggregator.build_guardians_response(
                guardians=all_data['guardians'],
                students_relations=all_data['students_relations'],
                students_academic=all_data['students_academic']
            )

            # 3. Enriquecer com boletos (PARALELO)
            logger.info("Enriching guardians with invoices")

            enrichment_service = GuardianEnrichmentService(token)
            guardians_enriched = enrichment_service.enrich_guardians_with_invoices(
                guardians_aggregated
            )

            # 4. Aplicar filtros
            if filters:
                logger.info(f"Applying filters: {filters}")
                guardians_filtered = GuardianFilterService.apply_filters(
                    guardians_enriched,
                    filters
                )
            else:
                guardians_filtered = guardians_enriched

            # 5. Serializar
            serializer = GuardianUnifiedSerializer(guardians_filtered, many=True)

            # 6. Cachear por 2 horas (7200 segundos)
            cache.set(cache_key, serializer.data, timeout=7200)
            logger.info(f"Cached data for {cache_key} (2 hours)")

            # 7. Aplicar paginação
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

    def _extract_filters(self, request) -> dict:
        """
        Extrai filtros da query string.

        Args:
            request: Request Django

        Returns:
            Dict com filtros aplicáveis
        """
        filters = {}

        # Search (nome, CPF, email, telefone, nome filho)
        search = request.query_params.get('search', '').strip()
        if search:
            filters['search'] = search

        # Email exato
        email = request.query_params.get('email', '').strip()
        if email:
            filters['email'] = email

        # CPF (com ou sem formatação)
        cpf = request.query_params.get('cpf', '').strip()
        if cpf:
            filters['cpf'] = cpf

        # Telefone (com ou sem formatação)
        telefone = request.query_params.get('telefone', '').strip()
        if telefone:
            filters['telefone'] = telefone

        # Tem boleto aberto (boolean)
        tem_boleto = request.query_params.get('tem_boleto_aberto', '').strip()
        if tem_boleto.lower() in ['true', '1', 'yes']:
            filters['tem_boleto_aberto'] = True
        elif tem_boleto.lower() in ['false', '0', 'no']:
            filters['tem_boleto_aberto'] = False

        # Tem doc faltando (boolean)
        tem_doc = request.query_params.get('tem_doc_faltando', '').strip()
        if tem_doc.lower() in ['true', '1', 'yes']:
            filters['tem_doc_faltando'] = True
        elif tem_doc.lower() in ['false', '0', 'no']:
            filters['tem_doc_faltando'] = False

        return filters

    def _generate_cache_key(self, school_id: int, filters: dict) -> str:
        """
        Gera cache key baseado em escola + filtros.

        Args:
            school_id: ID da escola
            filters: Dict de filtros

        Returns:
            String da cache key
        """
        # Base key
        key = f"guardians:unified:school:{school_id}"

        # Adicionar filtros (ordenados para consistência)
        if filters:
            filter_parts = []
            for k, v in sorted(filters.items()):
                filter_parts.append(f"{k}:{v}")

            filters_hash = ":".join(filter_parts)
            key += f":filters:{filters_hash}"

        return key