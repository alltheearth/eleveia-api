# eleveai/permissions.py
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão personalizada que permite:
    - Superusuários (admin): acesso total a todos os dados (CRUD completo)
    - Usuários comuns: CRUD completo apenas em seus próprios dados
    """

    def has_permission(self, request, view):
        """Verifica se o usuário tem permissão para acessar a view"""
        # Usuário deve estar autenticado
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Verifica se o usuário tem permissão para acessar o objeto específico"""
        # Superusuários podem fazer tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuários comuns podem fazer CRUD completo (incluindo DELETE) em seus próprios objetos
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user

        # Se não tem campo usuario, nega acesso
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite:
    - Leitura: todos os usuários autenticados
    - Escrita/Edição/Exclusão: apenas admin

    Útil para recursos compartilhados onde usuários podem ler,
    mas apenas admin pode modificar.
    """

    def has_permission(self, request, view):
        # Usuário deve estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # Métodos seguros (GET, HEAD, OPTIONS) são permitidos para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Outros métodos (POST, PUT, PATCH, DELETE) apenas para admin
        return request.user.is_superuser or request.user.is_staff