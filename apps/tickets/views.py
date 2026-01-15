# ===================================================================
# 4. apps/tickets/views.py - Tickets com Acesso por Dono
# ===================================================================
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket
from .serializers import TicketSerializer
from core.permissions import IsOwnerOrSchoolStaff
from core.mixins import UserOwnedMixin


class TicketViewSet(UserOwnedMixin, viewsets.ModelViewSet):
    """
    Tickets de suporte.

    Permissões:
    - End Users: Apenas seus próprios tickets
    - School Staff: Todos os tickets da escola
    - Superuser: Todos os tickets
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsOwnerOrSchoolStaff]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'priority', 'status']

    def perform_create(self, serializer):
        """Cria ticket vinculado ao usuário e escola"""
        extra_fields = {
            'created_by': self.request.user
        }

        # Se não é superuser, força a escola do usuário
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            if hasattr(self.request.user, 'profile'):
                extra_fields['school'] = self.request.user.profile.school

        serializer.save(**extra_fields)

    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        """Tickets do usuário autenticado"""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def open_tickets(self, request):
        """Tickets abertos (apenas staff)"""
        if not hasattr(request.user, 'profile'):
            return Response({'error': 'No profile'}, status=403)

        if not request.user.profile.is_school_staff():
            return Response({'error': 'Only staff can view all open tickets'}, status=403)

        queryset = self.get_queryset().filter(
            status__in=['open', 'in_progress']
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)