from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
PerfilUsuario
)

class PerfilUsuarioInline(admin.StackedInline):
    """Inline para editar perfil junto com User"""
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'usuario'
    extra = 0

    fields = ('escola', 'tipo', 'ativo')
    autocomplete_fields = ['escola']


class CustomUserAdmin(UserAdmin):
    """User Admin customizado com Perfil inline"""
    inlines = (PerfilUsuarioInline,)

    list_display = ('username', 'email', 'first_name', 'last_name', 'get_escola', 'get_tipo', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'perfil__tipo', 'perfil__escola')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def get_escola(self, obj):
        """Mostrar escola do usuário"""
        if hasattr(obj, 'perfil'):
            return obj.perfil.escola.nome_escola
        return '-'

    get_escola.short_description = 'Escola'
    get_escola.admin_order_field = 'perfil__escola__nome_escola'

    def get_tipo(self, obj):
        """Mostrar tipo do usuário"""
        if hasattr(obj, 'perfil'):
            return obj.perfil.get_tipo_display()
        return 'Admin' if obj.is_superuser else '-'

    get_tipo.short_description = 'Tipo'
    get_tipo.admin_order_field = 'perfil__tipo'


# Unregister default User admin e registrar customizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    """Admin para Perfis"""
    list_display = ('usuario', 'escola', 'tipo', 'ativo', 'criado_em')
    list_filter = ('tipo', 'ativo', 'escola', 'criado_em')
    search_fields = ('usuario__username', 'usuario__email', 'escola__nome_escola')
    autocomplete_fields = ['usuario', 'escola']
    readonly_fields = ('criado_em', 'atualizado_em')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'escola', 'tipo')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
