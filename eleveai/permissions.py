# eleveai/permissions.py
from rest_framework import permissions


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """
    Apenas superuser pode criar/editar/deletar
    Outros podem apenas ler
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escrita apenas para superuser
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
        """Verificar se tem permissão na view"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # CREATE - apenas superuser
        if request.method == 'POST':
            return False

        # Outros métodos precisam do perfil
        return hasattr(request.user, 'perfil')

    def has_object_permission(self, request, view, obj):
        """Verificar se tem permissão no objeto"""
        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuário deve ter perfil
        if not hasattr(request.user, 'perfil'):
            return False

        perfil = request.user.perfil

        # Só pode acessar escola vinculada
        if perfil.escola != obj:
            return False

        # Leitura permitida
        if request.method in permissions.SAFE_METHODS:
            return True

        # DELETE - apenas superuser
        if request.method == 'DELETE':
            return False

        # UPDATE - apenas gestor
        if request.method in ['PUT', 'PATCH']:
            return perfil.is_gestor()

        return False


class GestorOuOperadorPermission(permissions.BasePermission):
    """
    Permissões para modelos operacionais (Leads, Contatos, Eventos, FAQs):
    - Criar/Ler/Editar/Deletar: Gestor e Operador (apenas da sua escola)
    - Superuser: acesso total
    """

    def has_permission(self, request, view):
        """Verificar se tem permissão na view"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuário comum deve ter perfil
        return hasattr(request.user, 'perfil') and request.user.perfil.ativo

    def has_object_permission(self, request, view, obj):
        """Verificar se tem permissão no objeto"""
        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuário deve ter perfil
        if not hasattr(request.user, 'perfil'):
            return False

        perfil = request.user.perfil

        # Só pode acessar recursos da sua escola
        if hasattr(obj, 'escola') and perfil.escola != obj.escola:
            return False

        # Gestor e Operador podem fazer CRUD completo
        return perfil.ativo


class ApenasGestorPermission(permissions.BasePermission):
    """
    Permissões apenas para Gestor:
    Usado para operações sensíveis que apenas gestor pode fazer
    """

    def has_permission(self, request, view):
        """Verificar se tem permissão na view"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Deve ter perfil de gestor
        return (
                hasattr(request.user, 'perfil') and
                request.user.perfil.is_gestor() and
                request.user.perfil.ativo
        )

    def has_object_permission(self, request, view, obj):
        """Verificar se tem permissão no objeto"""
        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuário deve ter perfil
        if not hasattr(request.user, 'perfil'):
            return False

        perfil = request.user.perfil

        # Só pode acessar recursos da sua escola
        if hasattr(obj, 'escola') and perfil.escola != obj.escola:
            return False

        # Apenas gestor
        return perfil.is_gestor() and perfil.ativo


# ==========================================
# MIXINS ÚTEIS
# ==========================================

class UsuarioEscolaMixin:
    """
    Mixin para ViewSets que precisam filtrar por escola do usuário
    """

    def get_queryset(self):
        """
        Retorna queryset filtrado:
        - Superuser: tudo
        - Usuário comum: apenas da sua escola
        """
        queryset = super().get_queryset()

        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        if hasattr(self.request.user, 'perfil'):
            return queryset.filter(escola=self.request.user.perfil.escola)

        return queryset.none()

    def perform_create(self, serializer):
        """
        Ao criar, vincula automaticamente à escola do usuário
        """
        if hasattr(self.request.user, 'perfil'):
            serializer.save(
                usuario=self.request.user,
                escola=self.request.user.perfil.escola
            )
        else:
            # Se for superuser sem perfil, precisa informar escola
            serializer.save(usuario=self.request.user)


# ==========================================
# DECORATORS ÚTEIS
# ==========================================

def apenas_superuser(view_func):
    """
    Decorator para views que apenas superuser pode acessar
    """
    from functools import wraps
    from rest_framework.response import Response
    from rest_framework import status

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(
                {'erro': 'Apenas superusuários podem acessar este recurso'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def apenas_gestor(view_func):
    """
    Decorator para views que apenas gestor pode acessar
    """
    from functools import wraps
    from rest_framework.response import Response
    from rest_framework import status

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        if not hasattr(request.user, 'perfil'):
            return Response(
                {'erro': 'Usuário não possui perfil vinculado'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.perfil.is_gestor():
            return Response(
                {'erro': 'Apenas gestores podem acessar este recurso'},
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def gestor_ou_operador(view_func):
    """
    Decorator para views que gestor ou operador podem acessar
    """
    from functools import wraps
    from rest_framework.response import Response
    from rest_framework import status

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        if not hasattr(request.user, 'perfil'):
            return Response(
                {'erro': 'Usuário não possui perfil vinculado'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.perfil.ativo:
            return Response(
                {'erro': 'Usuário inativo'},
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)

    return wrapper