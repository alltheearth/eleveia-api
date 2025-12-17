# eleveai/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Escola, Contato, CalendarioEvento, FAQ, Dashboard,
    Documento, Lead, PerfilUsuario
)


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
