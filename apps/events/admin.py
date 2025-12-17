# eleveai/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
 CalendarioEvento
)


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
