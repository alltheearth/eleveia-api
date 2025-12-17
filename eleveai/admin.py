# eleveai/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Escola, Contato, CalendarioEvento, FAQ, Dashboard,
    Documento, Lead, PerfilUsuario
)


# ==========================================
# PERFIL DE USUÁRIO
# ==========================================

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


# ==========================================
# ESCOLA
# ==========================================

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


# ==========================================
# CONTATOS
# ==========================================

@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    """Admin para Contatos"""
    list_display = ('nome', 'email', 'telefone', 'status', 'origem', 'escola', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'escola__nome_escola', 'tags')
    list_filter = ('status', 'origem', 'escola', 'criado_em')
    readonly_fields = ('criado_em', 'atualizado_em')
    autocomplete_fields = ['escola', 'usuario']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'escola', 'nome', 'email', 'telefone', 'data_nascimento')
        }),
        ('Status e Origem', {
            'fields': ('status', 'origem')
        }),
        ('Detalhes', {
            'fields': ('observacoes', 'tags', 'ultima_interacao')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)
    list_per_page = 50


# ==========================================
# LEADS
# ==========================================

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin para Leads"""
    list_display = ('nome', 'email', 'telefone', 'status', 'origem', 'escola', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'escola__nome_escola')
    list_filter = ('status', 'origem', 'escola', 'criado_em')
    readonly_fields = ('criado_em', 'atualizado_em', 'contatado_em', 'convertido_em')
    autocomplete_fields = ['escola', 'usuario']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'escola', 'nome', 'email', 'telefone')
        }),
        ('Status e Origem', {
            'fields': ('status', 'origem')
        }),
        ('Detalhes', {
            'fields': ('observacoes', 'interesses')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em', 'contatado_em', 'convertido_em'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)


# ==========================================
# CALENDÁRIO
# ==========================================

@admin.register(CalendarioEvento)
class CalendarioEventoAdmin(admin.ModelAdmin):
    """Admin para Eventos"""
    list_display = ('evento', 'data', 'tipo', 'escola', 'criado_em')
    search_fields = ('evento', 'escola__nome_escola')
    list_filter = ('tipo', 'data', 'escola')
    ordering = ('-data',)
    readonly_fields = ('criado_em', 'atualizado_em')
    autocomplete_fields = ['escola', 'usuario']

    fieldsets = (
        ('Evento', {
            'fields': ('usuario', 'escola', 'evento', 'data', 'tipo')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


# ==========================================
# FAQ
# ==========================================

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin para FAQs"""
    list_display = ('pergunta', 'categoria', 'status', 'escola', 'criado_em')
    search_fields = ('pergunta', 'resposta', 'categoria', 'escola__nome_escola')
    list_filter = ('status', 'categoria', 'escola', 'criado_em')
    readonly_fields = ('criado_em', 'atualizado_em')
    autocomplete_fields = ['escola', 'usuario']

    fieldsets = (
        ('FAQ', {
            'fields': ('usuario', 'escola', 'pergunta', 'resposta', 'categoria', 'status')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


# ==========================================
# DOCUMENTOS
# ==========================================

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """Admin para Documentos"""
    list_display = ('nome', 'escola', 'status', 'criado_em')
    search_fields = ('nome', 'escola__nome_escola')
    list_filter = ('status', 'criado_em', 'escola')
    readonly_fields = ('criado_em', 'atualizado_em')
    autocomplete_fields = ['escola', 'usuario']

    fieldsets = (
        ('Documento', {
            'fields': ('usuario', 'escola', 'nome', 'arquivo', 'status')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


# ==========================================
# DASHBOARD
# ==========================================

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin para Dashboard"""
    list_display = ('escola', 'status_agente', 'interacoes_hoje', 'leads_capturados', 'atualizado_em')
    search_fields = ('escola__nome_escola',)
    list_filter = ('status_agente', 'escola')
    readonly_fields = ('atualizado_em',)
    autocomplete_fields = ['escola', 'usuario']

    fieldsets = (
        ('Escola', {
            'fields': ('usuario', 'escola', 'status_agente')
        }),
        ('Métricas', {
            'fields': (
                'interacoes_hoje', 'documentos_upload', 'faqs_criadas',
                'leads_capturados', 'taxa_resolucao', 'novos_hoje'
            )
        }),
        ('Timestamps', {
            'fields': ('atualizado_em',),
            'classes': ('collapse',)
        }),
    )


# ==========================================
# CUSTOMIZAÇÕES DO ADMIN
# ==========================================

# Título do Admin
admin.site.site_header = "EleveAI Admin"
admin.site.site_title = "EleveAI"
admin.site.index_title = "Gestão de Escolas"