# eleveai/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Escola, Contato, CalendarioEvento, FAQ, Dashboard,
    Documento, Lead, PerfilUsuario
)

class UsuarioEscolaInline(admin.TabularInline):
    """Inline para mostrar usuários da escola"""
    model = PerfilUsuario
    extra = 0
    fields = ('usuario', 'tipo', 'ativo')
    readonly_fields = ('usuario',)
    can_delete = False


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    """Admin para Escola"""
    list_display = ('nome_escola', 'cnpj', 'cidade', 'estado', 'get_total_usuarios', 'criado_em')
    search_fields = ('nome_escola', 'cnpj', 'cidade', 'email')
    list_filter = ('cidade', 'estado', 'criado_em')
    readonly_fields = ('criado_em', 'atualizado_em')

    inlines = [UsuarioEscolaInline]

    fieldsets = (
        ('⚠️ Campos Protegidos (apenas superuser)', {
            'fields': ('nome_escola', 'cnpj', 'token_mensagens'),
            'classes': ('wide',),
            'description': 'Estes campos só podem ser alterados por superusuários'
        }),
        ('Informações de Contato', {
            'fields': ('telefone', 'email', 'website', 'logo')
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'complemento', 'cidade', 'estado')
        }),
        ('Sobre a Escola', {
            'fields': ('sobre', 'niveis_ensino')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def get_total_usuarios(self, obj):
        """Total de usuários da escola"""
        return obj.usuarios.count()

    get_total_usuarios.short_description = 'Usuários'

    def save_model(self, request, obj, form, change):
        """Validação extra ao salvar"""
        if change:  # Se for edição
            if not request.user.is_superuser:
                # Bloqueia alteração de campos protegidos
                original = Escola.objects.get(pk=obj.pk)
                obj.nome_escola = original.nome_escola
                obj.cnpj = original.cnpj
                obj.token_mensagens = original.token_mensagens

        super().save_model(request, obj, form, change)
