# ===================================================================
# apps/leads/views.py - VERSÃO CORRIGIDA
# ===================================================================
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Lead
from .serializers import LeadSerializer
from core.permissions import IsSchoolStaff
from core.mixins import SchoolIsolationMixin


class LeadViewSet(SchoolIsolationMixin, viewsets.ModelViewSet):
    """
    ViewSet para Leads.

    Leads capturados pelo agente IA ou outros canais.

    Permissões:
    - School Staff: CRUD completo na sua escola
    - Superuser: Acesso a todos os leads
    """
    queryset = Lead.objects.select_related('school')
    serializer_class = LeadSerializer
    permission_classes = [IsSchoolStaff]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'email', 'telephone', 'status', 'origin']
    ordering_fields = ['name', 'status', 'created_at', 'converted_at']

    def get_queryset(self):
        """Filtros adicionais"""
        queryset = super().get_queryset()

        # Filtro por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filtro por origem
        origin_param = self.request.query_params.get('origin')
        if origin_param:
            queryset = queryset.filter(origin=origin_param)

        return queryset