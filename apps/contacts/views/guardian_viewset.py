# apps/contacts/views/guardian_viewset.py

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
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class GuardianViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gerenciamento de Guardians."""

    permission_classes = [IsSchoolStaff]
    pagination_class = GuardianPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return GuardianListSerializer
        return GuardianDetailSerializer

    @extend_schema(
        summary="Lista guardians da escola",
        parameters=[
            OpenApiParameter(name='search', description='Busca por nome/CPF/filho', type=str),
            OpenApiParameter(name='cpf', description='Filtro exato por CPF', type=str),
            OpenApiParameter(name='ordering', description='Ordenação (nome, -nome)', type=str),
        ],
        tags=['Guardians']
    )
    def list(self, request):
        """GET /api/v1/contacts/guardians/"""
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response({"error": "Usuário sem escola vinculada"}, status=403)

        school = request.user.profile.school
        token = school.application_token

        if not token:
            return Response({"error": "Escola sem token configurado"}, status=500)

        try:
            guardians = GuardianService.get_guardians_list(school.id, token)

            search = request.query_params.get('search', '').strip()
            cpf = request.query_params.get('cpf', '').strip()
            ordering = request.query_params.get('ordering', 'nome')

            if search:
                guardians = GuardianSelector.filter_by_search(guardians, search)
            if cpf:
                guardians = GuardianSelector.filter_by_cpf(guardians, cpf)

            guardians = GuardianSelector.order_by(guardians, ordering)

            page = self.paginate_queryset(guardians)
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response(serializer.data)

        except Exception as e:
            logger.exception(f"Error listing guardians: {e}")
            return Response({"error": "Erro ao buscar guardians"}, status=500)

    @extend_schema(
        summary="Detalhes completos de um guardian",
        tags=['Guardians']
    )
    def retrieve(self, request, pk=None):
        """GET /api/v1/contacts/guardians/{id}/"""
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response({"error": "Usuário sem escola vinculada"}, status=403)

        school = request.user.profile.school
        token = school.application_token

        try:
            guardian_id = int(pk)
            guardian = GuardianService.get_guardian_detail(guardian_id, school.id, token, True)

            if not guardian:
                return Response({"error": "Guardian não encontrado"}, status=404)

            serializer = self.get_serializer(guardian)
            return Response(serializer.data)

        except Exception as e:
            logger.exception(f"Error retrieving guardian {pk}: {e}")
            return Response({"error": "Erro ao buscar guardian"}, status=500)

    @extend_schema(summary="Resumo de boletos", tags=['Guardians'])
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """GET /api/v1/contacts/guardians/{id}/invoices/"""
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response({"error": "Usuário sem escola vinculada"}, status=403)

        school = request.user.profile.school
        token = school.application_token

        try:
            guardian_id = int(pk)
            guardian = GuardianService.get_guardian_detail(guardian_id, school.id, token, True)

            if not guardian:
                return Response({"error": "Guardian não encontrado"}, status=404)

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

            return Response(result)

        except Exception as e:
            logger.exception(f"Error getting invoices: {e}")
            return Response({"error": "Erro ao buscar boletos"}, status=500)