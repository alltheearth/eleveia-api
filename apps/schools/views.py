# ===================================================================
# apps/schools/views.py - CORRIGIDO COMPLETAMENTE
# ===================================================================
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import School
from .serializers import SchoolSerializer, SchoolPublicSerializer
from core.permissions import SchoolPermission


class SchoolViewSet(viewsets.ModelViewSet):
    """
    Gestão de Escolas.

    IMPORTANTE: NÃO USA SchoolIsolationMixin porque School não tem
    campo 'school' - a lógica de isolamento é customizada aqui.

    Permissões:
    - CREATE: Apenas superuser
    - READ: Superuser (todas) ou usuário vinculado (apenas sua escola)
    - UPDATE: Superuser (tudo) ou Manager (campos não-super-protegidos)
    - DELETE: Apenas superuser
    """
    queryset = School.objects.all()
    permission_classes = [SchoolPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['school_name', 'city', 'state', 'tax_id']
    ordering_fields = ['school_name', 'created_at']

    def get_queryset(self):
        """
        Filtro customizado para School.

        - Superuser: vê todas as escolas
        - Manager/Operator/EndUser: vê apenas a escola vinculada
        """
        queryset = super().get_queryset()

        # Superuser vê todas
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        # Usuário precisa ter perfil
        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        profile = self.request.user.profile

        # Verifica se está ativo
        if not profile.is_active:
            return queryset.none()

        # Filtra pela escola do perfil
        if profile.school:
            # ✅ CORREÇÃO: Filtra por ID, não por campo 'school'
            return queryset.filter(id=profile.school.id)

        return queryset.none()

    def get_serializer_class(self):
        """End users veem versão pública"""
        if hasattr(self.request.user, 'profile'):
            if self.request.user.profile.is_end_user():
                return SchoolPublicSerializer
        return SchoolSerializer

    def perform_create(self, serializer):
        """
        Cria escola SEM created_by (School não tem esse campo).
        Apenas superusers podem criar escolas.
        """
        # School não tem created_by, então não passamos extra_fields
        serializer.save()

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
            'total_documents': school.documents.count(),
            'total_tickets': school.tickets.count(),
            'total_leads': school.leads.count(),
        }

        return Response(stats)

    @action(detail=False, methods=['get'])
    def my_school(self, request):
        """
        Retorna a escola do usuário autenticado.
        Útil para frontend pegar dados da escola sem saber o ID.
        """
        if not hasattr(request.user, 'profile') or not request.user.profile.school:
            return Response(
                {'error': 'User has no associated school'},
                status=404
            )

        school = request.user.profile.school
        serializer = self.get_serializer(school)
        return Response(serializer.data)