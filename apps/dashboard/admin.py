# eleveai/admin.py
from django.contrib import admin
from .models import (
 Dashboard
)

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

