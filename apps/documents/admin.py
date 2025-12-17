# eleveai/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (

    Documento
)

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
