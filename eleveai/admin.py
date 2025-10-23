from django.contrib import admin

from django.contrib import admin
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento, Lead

@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ('nome_escola', 'cnpj', 'cidade', 'criado_em')
    search_fields = ('nome_escola', 'cnpj', 'cidade')
    list_filter = ('cidade', 'estado', 'criado_em')


@admin.register(Contato)
class ContatoGeralAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'email', 'telefone', 'status', 'origem', 'escola', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'escola__nome_escola', 'tags')
    list_filter = ('status', 'origem', 'escola', 'criado_em')
    readonly_fields = ('criado_em', 'atualizado_em')

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

@admin.register(CalendarioEvento)
class CalendarioEventoAdmin(admin.ModelAdmin):
    list_display = ('escola', 'evento', 'data', 'tipo')
    search_fields = ('evento', 'escola__nome_escola')
    list_filter = ('tipo', 'data', 'escola')
    ordering = ('-data',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('pergunta', 'categoria', 'status', 'escola')
    search_fields = ('pergunta', 'categoria', 'escola__nome_escola')
    list_filter = ('status', 'categoria', 'escola')

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'escola', 'status', 'criado_em')
    search_fields = ('nome', 'escola__nome_escola')
    list_filter = ('status', 'criado_em', 'escola')

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('escola', 'status_agente', 'interacoes_hoje', 'leads_capturados')
    search_fields = ('escola__nome_escola',)
    readonly_fields = ('atualizado_em',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'status', 'origem', 'escola', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'escola__nome_escola')
    list_filter = ('status', 'origem', 'escola', 'criado_em')
    readonly_fields = ('criado_em', 'atualizado_em', 'contatado_em', 'convertido_em')

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