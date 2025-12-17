# ===== apps/dashboard/views.py =====
from rest_framework import viewsets

from .models import Dashboard
from .serializers import DashboardSerializer
from core.permissions import GestorOuOperadorPermission


class DashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Dashboard
    Todos podem visualizar o dashboard da sua escola
    """
    serializer_class = DashboardSerializer
    permission_classes = [GestorOuOperadorPermission]

    def get_queryset(self):
        """Retorna dashboard da escola do usuário"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Dashboard.objects.all()

        if hasattr(self.request.user, 'perfil'):
            return Dashboard.objects.filter(escola=self.request.user.perfil.escola)

        return Dashboard.objects.none()


