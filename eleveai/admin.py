from django.contrib import admin

from django.contrib import admin
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento

@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ('nome_escola', 'cnpj', 'cidade', 'criado_em')
    search_fields = ('nome_escola', 'cnpj', 'cidade')
    list_filter = ('cidade', 'estado', 'criado_em')

@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ('escola', 'email_principal', 'telefone_principal')
    search_fields = ('escola__nome_escola', 'email_principal')

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
