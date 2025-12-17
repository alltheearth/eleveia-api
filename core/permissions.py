"""
Permissões reutilizáveis do sistema
"""
from rest_framework import permissions


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """Apenas superuser pode criar/editar/deletar. Outros podem ler."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser or request.user.is_staff


class EscolaPermission(permissions.BasePermission):
    """
    Permissões para o modelo Escola:
    - Criar: Apenas superuser
    - Ler: Superuser (todas) ou usuários vinculados (sua escola)
    - Editar: Superuser (tudo) ou Gestor (campos não protegidos)
    - Deletar: Apenas superuser
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        if request.method == 'POST':
            return False

        return hasattr(request.user, 'perfil')

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        if not hasattr(request.user, 'perfil'):
            return False

        perfil = request.user.perfil

        if perfil.escola != obj:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method == 'DELETE':
            return False

        if request.method in ['PUT', 'PATCH']:
            return perfil.is_gestor()

        return False


class GestorOuOperadorPermission(permissions.BasePermission):
    """
    Permissões para operações do dia-a-dia
    Gestor e Operador podem CRUD na sua escola
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        return hasattr(request.user, 'perfil') and request.user.perfil.ativo

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        if not hasattr(request.user, 'perfil'):
            return False

        perfil = request.user.perfil

        if hasattr(obj, 'escola') and perfil.escola != obj.escola:
            return False

        return perfil.ativo


class ApenasGestorPermission(permissions.BasePermission):
    """Apenas gestor ou superuser"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        return (
                hasattr(request.user, 'perfil') and
                request.user.perfil.is_gestor() and
                request.user.perfil.ativo
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        if not hasattr(request.user, 'perfil'):
            return False

        perfil = request.user.perfil

        if hasattr(obj, 'escola') and perfil.escola != obj.escola:
            return False

        return perfil.is_gestor() and perfil.ativo