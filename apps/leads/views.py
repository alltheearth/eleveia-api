from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Lead
from .serializers import LeadSerializer

from core.permissions import EscolaPermission


class TicketViewSet(viewsets.ModelViewSet):
    """ViewSet para Ticket"""
    serializer_class = LeadSerializer
    permission_classes = [EscolaPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'status']
    ordering_fields = ['title', 'create_at']

    def get_queryset(self):
        """Retorna tickets conforme permissão"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Lead.objects.all()

        if hasattr(self.request.user, 'perfil'):
            return Lead.objects.filter(id=self.request.user.perfil.escola.id)

        return Lead.objects.none()


