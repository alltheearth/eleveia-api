# apps/dashboard/admin.py
from django.contrib import admin
from .models import DashboardMetrics, InteracaoN8N


@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(admin.ModelAdmin):
    list_display = (
        'escola', 'total_interacoes', 'interacoes_hoje',
        'leads_capturados', 'status_agente', 'atualizado_em'
    )
    list_filter = ('status_agente', 'escola', 'atualizado_em')
    search_fields = ('escola__nome_escola',)
    readonly_fields = ('criado_em', 'atualizado_em')

    fieldsets = (
        ('Escola', {
            'fields': ('escola',)
        }),
        ('Métricas', {
            'fields': (
                'total_interacoes', 'interacoes_hoje',
                'leads_capturados', 'tickets_abertos',
            )
        }),
        ('Performance', {
            'fields': (
                'tempo_medio_resposta', 'taxa_satisfacao', 'taxa_conversao',
            )
        }),
        ('Status', {
            'fields': ('status_agente',)
        }),
        ('N8N', {
            'fields': ('n8n_workflow_id', 'n8n_execution_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InteracaoN8N)
class InteracaoN8NAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'titulo', 'escola', 'criado_em')
    list_filter = ('tipo', 'escola', 'criado_em')
    search_fields = ('titulo', 'descricao', 'escola__nome_escola')
    readonly_fields = ('criado_em',)

    fieldsets = (
        ('Informações', {
            'fields': ('escola', 'tipo', 'titulo', 'descricao')
        }),
        ('Dados', {
            'fields': ('dados',)
        }),
        ('N8N', {
            'fields': ('n8n_workflow_id', 'n8n_execution_id'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('criado_em',)
        }),
    )