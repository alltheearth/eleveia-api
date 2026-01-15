# ===================================================================
# 5. apps/users/views.py - Gestão de Perfis
# ===================================================================
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import UserProfile
from .serializers import UserProfileSerializer
from core.permissions import IsManager
from core.mixins import OnlySelfAccessMixin


class UserProfileViewSet(OnlySelfAccessMixin, viewsets.ModelViewSet):
    """
    Perfis de usuários.

    Permissões:
    - End User: Apenas próprio perfil (read-only)
    - Manager: Todos os perfis da escola
    - Superuser: Todos os perfis
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Permissões dinâmicas por ação"""
        if self.action in ['create', 'destroy']:
            # Criar/deletar usuários: apenas managers
            return [IsManager()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Perfil do usuário autenticado"""
        if not hasattr(request.user, 'profile'):
            return Response(
                {'error': 'User has no profile'},
                status=404
            )

        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def school_users(self, request):
        """Lista usuários da escola (apenas managers)"""
        if not hasattr(request.user, 'profile'):
            return Response({'error': 'No profile'}, status=403)

        if not request.user.profile.is_manager():
            return Response({'error': 'Only managers'}, status=403)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)