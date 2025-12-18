from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Ticket
from .serializers import TicketSerializer
from core.permissions import EscolaPermission


class TicketViewSet(viewsets.ModelViewSet):
    """ViewSet para Ticket"""
    serializer_class = TicketSerializer
    permission_classes = [EscolaPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'status']
    ordering_fields = ['title', 'create_at']

    def get_queryset(self):
        """Retorna tickets conforme permissão"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Ticket.objects.all()

        if hasattr(self.request.user, 'perfil'):
            return Ticket.objects.filter(id=self.request.user.perfil.escola.id)

        return Ticket.objects.none()


