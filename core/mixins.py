# ===================================================================
# core/mixins.py - MIXINS REFATORADOS COM ISOLAMENTO TOTAL
# ===================================================================
from django.db.models import Q


class SchoolIsolationMixin:
    """
    Isola completamente os dados por escola.

    Comportamento:
    - Superuser: vê tudo
    - Manager/Operator: vê apenas da sua escola
    - End User: vê apenas da sua escola (filtrado posteriormente por IsOwner)

    IMPORTANTE: Este mixin SEMPRE deve vir ANTES de viewsets.ModelViewSet
    """

    def get_queryset(self):
        """Filtra queryset pela escola do usuário"""
        queryset = super().get_queryset()

        # Superuser vê tudo
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        # Usuário precisa ter perfil
        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        profile = self.request.user.profile

        # Verifica se está ativo
        if not profile.is_active:
            return queryset.none()

        # Filtra pela escola do usuário
        if profile.school:
            return queryset.filter(school=profile.school)

        return queryset.none()

    def perform_create(self, serializer):
        """
        Vincula automaticamente à escola do usuário na criação.
        Define created_by se o model tiver esse campo.
        """
        extra_fields = {'created_by': self.request.user}

        # Superuser pode criar em qualquer escola (deve passar school_id)
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            if hasattr(self.request.user, 'profile') and self.request.user.profile.school:
                extra_fields['school'] = self.request.user.profile.school

        serializer.save(**extra_fields)


class UserOwnedMixin:
    """
    Para recursos que pertencem a um usuário específico.
    End users só veem os próprios, staff da escola vê todos da escola.

    Exemplo: Tickets criados por end_users
    """

    def get_queryset(self):
        """Filtra por dono + escola"""
        queryset = super().get_queryset()

        # Superuser vê tudo
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        profile = self.request.user.profile

        if not profile.is_active:
            return queryset.none()

        # Staff da escola vê tudo da escola
        if profile.is_school_staff():
            return queryset.filter(school=profile.school)

        # End user vê apenas o que criou
        if profile.is_end_user():
            return queryset.filter(
                Q(school=profile.school) &
                (Q(created_by=self.request.user) | Q(user=self.request.user))
            )

        return queryset.none()


class ReadOnlyForEndUserMixin:
    """
    End users podem apenas ler (GET).
    Staff da escola pode CRUD.

    Exemplo: FAQs, Eventos
    """

    def get_queryset(self):
        """Aplica filtro de escola"""
        queryset = super().get_queryset()

        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        profile = self.request.user.profile

        if not profile.is_active or not profile.school:
            return queryset.none()

        return queryset.filter(school=profile.school)

    def check_object_permissions(self, request, obj):
        """End users não podem modificar"""
        super().check_object_permissions(request, obj)

        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            if hasattr(request.user, 'profile'):
                if request.user.profile.is_end_user():
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied(
                        "End users can only read this resource."
                    )


class OnlySelfAccessMixin:
    """
    Usuário só pode acessar o próprio perfil/dados.
    Superuser e Managers podem acessar outros perfis.

    Exemplo: UserProfile, dados pessoais
    """

    def get_queryset(self):
        """Filtra por usuário ou escola (para managers)"""
        queryset = super().get_queryset()

        # Superuser vê tudo
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        profile = self.request.user.profile

        # Manager vê todos da sua escola
        if profile.is_manager():
            return queryset.filter(school=profile.school)

        # Operator e End User veem apenas a si mesmos
        return queryset.filter(user=self.request.user)


class SchoolStatsMixin:
    """
    Mixin para views de estatísticas/dashboards.
    Retorna estatísticas apenas da escola do usuário.
    """

    def get_school_filter(self):
        """Retorna Q object para filtrar por escola"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            # Superuser pode filtrar por school_id query param
            school_id = self.request.query_params.get('school_id')
            if school_id:
                return Q(school_id=school_id)
            return Q()  # Sem filtro = todas as escolas

        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            if profile.school:
                return Q(school=profile.school)

        return Q(pk__in=[])  # Nenhum resultado


# ===================================================================
# MIXINS DE PERFORMANCE
# ===================================================================

class OptimizedQueryMixin:
    """
    Otimiza queries com select_related e prefetch_related.
    Sobrescreva select_related_fields e prefetch_related_fields nas views.
    """

    select_related_fields = []
    prefetch_related_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        return queryset


# ===================================================================
# MIXIN EXEMPLO DE USO COMBINADO
# ===================================================================

class SchoolResourceViewSet:
    """
    Base ViewSet para recursos da escola.
    Combina isolamento + otimização.

    Uso:
        class FAQViewSet(SchoolResourceViewSet, viewsets.ModelViewSet):
            queryset = FAQ.objects.all()
            serializer_class = FAQSerializer
            permission_classes = [IsSchoolStaff]
            select_related_fields = ['school', 'created_by']
    """
    pass

# Para usar, o ViewSet deve herdar assim:
# class MyViewSet(SchoolIsolationMixin, OptimizedQueryMixin, viewsets.ModelViewSet)