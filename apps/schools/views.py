# ===================================================================
# 1. apps/schools/views.py
# ===================================================================
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import School
from .serializers import SchoolSerializer, SchoolPublicSerializer
from core.permissions import SchoolPermission
from core.mixins import SchoolIsolationMixin, OptimizedQueryMixin


class SchoolViewSet(
    SchoolIsolationMixin,
    OptimizedQueryMixin,
    viewsets.ModelViewSet
):
    """
    Gestão de Escolas.

    Permissões:
    - CREATE: Apenas superuser
    - READ: Superuser (todas) ou usuário vinculado (apenas sua escola)
    - UPDATE: Superuser (tudo) ou Manager (campos não-super-protegidos)
    - DELETE: Apenas superuser
    """
    queryset = School.objects.all()
    permission_classes = [SchoolPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['school_name', 'city', 'state']
    ordering_fields = ['school_name', 'created_at']

    select_related_fields = []  # School não tem FKs
    prefetch_related_fields = []

    def get_serializer_class(self):
        """End users veem versão pública"""
        if hasattr(self.request.user, 'profile'):
            if self.request.user.profile.is_end_user():
                return SchoolPublicSerializer
        return SchoolSerializer

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Estatísticas da escola (apenas staff)"""
        school = self.get_object()

        # Verifica permissão
        if not (request.user.is_superuser or
                (hasattr(request.user, 'profile') and
                 request.user.profile.is_school_staff())):
            return Response(
                {'error': 'Only school staff can view statistics'},
                status=403
            )

        stats = {
            'total_users': school.user_profiles.filter(is_active=True).count(),
            'total_contacts': school.whatsapp_contacts.count(),
            'total_events': school.calendar_events.count(),
            'total_faqs': school.faqs.filter(status='active').count(),
        }

        return Response(stats)
