"""
Mixins reutilizáveis para ViewSets
"""


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
            serializer.save(usuario=self.request.user)


class TimestampMixin:
    """
    Mixin para adicionar timestamps automáticos
    """
    criado_em = None
    atualizado_em = None

    def save(self, *args, **kwargs):
        """Adiciona timestamps antes de salvar"""
        super().save(*args, **kwargs)