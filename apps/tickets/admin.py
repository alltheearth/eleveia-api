# ===================================================================
# apps/tickets/admin.py - CORRIGIDO
# ===================================================================
from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin for Tickets"""

    list_display = ['title', 'status', 'priority', 'school', 'created_at']
    list_filter = ['status', 'priority', 'school', 'created_at']
    search_fields = ['title', 'description', 'school__school_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Ticket', {
            'fields': ('school', 'title', 'description', 'status', 'priority'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
