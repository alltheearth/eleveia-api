# apps/contacts/views/guardian_views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..serializers import GuardianDetailSerializer
from ..services import SigaIntegrationService, SigaIntegrationError

import logging

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
            500: OpenApiResponse(description="Erro ao buscar dados da API externa"),
        },
        tags=['Responsáveis']
    )
    def get(self, request, *args, **kwargs):
        """
        GET /api/v1/contacts/guardians/

        Lista todos os responsáveis com seus filhos.
        """
        try:
            # Validação de token da escola
            if not hasattr(request.user, 'profile') or not request.user.profile.school:
                return Response(
                    {'error': 'Usuário sem escola vinculada'},
                    status=status.HTTP_403_FORBIDDEN
                )

            school = request.user.profile.school

            if not school.application_token:
                return Response(
                    {'error': 'Escola sem token SIGA configurado'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Buscar dados via service layer
            service = SigaIntegrationService(token=school.application_token)
            guardians_data = service.get_all_guardians_enriched()

            # Aplicar paginação
            paginator = self.pagination_class()
            paginated_guardians = paginator.paginate_queryset(
                guardians_data,
                request
            )

            # Serializar dados
            serializer = GuardianDetailSerializer(
                paginated_guardians,
                many=True
            )

            # Retornar resposta paginada
            return paginator.get_paginated_response(serializer.data)

        except SigaIntegrationError as e:
            logger.error(f"Erro de integração SIGA: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Erro ao buscar dados dos responsáveis',
                    'detail': str(e)
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Erro ao buscar dados dos responsáveis',
                    'detail': str(e) if request.user.is_staff else 'Erro interno do servidor'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )