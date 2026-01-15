# ===================================================================
# core/permissions.py - SISTEMA COMPLETO DE PERMISSÕES
# ===================================================================
from rest_framework import permissions


# ===================================================================
# PERMISSÕES BASE
# ===================================================================

class IsSuperuser(permissions.BasePermission):
    """Apenas superusuários"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff)
        )


class IsAuthenticated(permissions.BasePermission):
    """Apenas usuários autenticados"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


# ===================================================================
# PERMISSÕES POR NÍVEL DE ACESSO
# ===================================================================

class IsSchoolStaff(permissions.BasePermission):
    """
    Manager ou Operator da escola.
    Superuser também tem acesso.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser sempre tem acesso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verifica se tem perfil ativo
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        return profile.is_school_staff() and profile.is_active

    def has_object_permission(self, request, view, obj):
        """Verifica acesso ao objeto específico"""
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Verifica se o objeto pertence à escola do usuário
        if hasattr(obj, 'school'):
            return profile.school == obj.school and profile.is_active
        
        return False


class IsManager(permissions.BasePermission):
    """
    Apenas Manager da escola.
    Superuser também tem acesso.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        return request.user.profile.is_manager()

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        if hasattr(obj, 'school'):
            return (
                profile.is_manager() and 
                profile.school == obj.school and 
                profile.is_active
            )
        
        return False


class IsOperator(permissions.BasePermission):
    """
    Apenas Operator da escola.
    Superuser e Manager também têm acesso.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        return profile.is_operator() or profile.is_manager()


class IsEndUser(permissions.BasePermission):
    """
    Apenas End User (cliente/aluno).
    Usado raramente - geralmente combinado com IsOwner.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        return request.user.profile.is_end_user()


# ===================================================================
# PERMISSÕES DE PROPRIEDADE
# ===================================================================

class IsOwner(permissions.BasePermission):
    """
    Usuário é dono do objeto.
    Verifica campos: user, created_by, owner
    """
    
    def has_object_permission(self, request, view, obj):
        # Superuser sempre tem acesso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verifica diferentes campos de ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsOwnerOrSchoolStaff(permissions.BasePermission):
    """
    Dono do objeto OU staff da escola.
    Ideal para tickets, onde end_user pode ver os seus
    e staff da escola pode ver todos da escola.
    """
    
    def has_object_permission(self, request, view, obj):
        # Superuser sempre tem acesso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Staff da escola vê tudo da escola
        if profile.is_school_staff() and hasattr(obj, 'school'):
            return profile.school == obj.school
        
        # End user vê apenas o que criou
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


# ===================================================================
# PERMISSÕES PARA ESCOLA
# ===================================================================

class SchoolPermission(permissions.BasePermission):
    """
    Permissões específicas para o model School:
    
    - CREATE: Apenas superuser
    - READ: Superuser (todas) ou usuário da escola (apenas sua escola)
    - UPDATE: Superuser (tudo) ou Manager (campos não-protegidos)
    - DELETE: Apenas superuser
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Criar escola: apenas superuser
        if request.method == 'POST':
            return False
        
        # Precisa ter perfil
        return hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Só pode acessar a própria escola
        if profile.school != obj:
            return False
        
        # READ: todos da escola
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # DELETE: apenas superuser (já verificado acima)
        if request.method == 'DELETE':
            return False
        
        # UPDATE: apenas managers (campos não-protegidos são validados no serializer)
        if request.method in ['PUT', 'PATCH']:
            return profile.is_manager() and profile.is_active
        
        return False


# ===================================================================
# PERMISSÕES COMBINADAS (COMPOSTAS)
# ===================================================================

class ReadOnlyOrSchoolStaff(permissions.BasePermission):
    """
    Leitura para todos autenticados da escola.
    Edição apenas para staff da escola.
    
    Ideal para: FAQs públicas, Eventos públicos
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser pode tudo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Precisa ter perfil
        if not hasattr(request.user, 'profile'):
            return False
        
        # Leitura: todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escrita: apenas staff
        return request.user.profile.is_school_staff()

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Verifica se pertence à mesma escola
        if hasattr(obj, 'school'):
            if profile.school != obj.school:
                return False
        
        # Leitura: todos da escola
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escrita: apenas staff
        return profile.is_school_staff()


# ===================================================================
# MAPEAMENTO DE PERMISSÕES POR RECURSO
# ===================================================================

PERMISSION_MAP = {
    # Gestão de escolas
    'school': SchoolPermission,
    
    # Staff da escola pode CRUD
    'faq': IsSchoolStaff,
    'document': IsSchoolStaff,
    'event': IsSchoolStaff,
    'lead': IsSchoolStaff,
    
    # Staff ou dono (para tickets de end_user)
    'ticket': IsOwnerOrSchoolStaff,
    
    # Apenas managers
    'user_management': IsManager,
    
    # Todos da escola podem ler, staff pode editar
    'public_content': ReadOnlyOrSchoolStaff,
}