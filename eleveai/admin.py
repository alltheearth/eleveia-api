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



# ==========================================
# ESCOLA
# ==========================================



# ==========================================
# CONTATOS
# ==========================================



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


# ==========================================
# FAQ
# ==========================================



# ==========================================
# DOCUMENTOS
# ==========================================



# ==========================================
# DASHBOARD
# ==========================================



# ==========================================
# CUSTOMIZAÇÕES DO ADMIN
# ==========================================

# Título do Admin
admin.site.site_header = "EleveAI Admin"
admin.site.site_title = "EleveAI"
admin.site.index_title = "Gestão de Escolas"