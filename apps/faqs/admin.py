# eleveai/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
 FAQ

)

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
