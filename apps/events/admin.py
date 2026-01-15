# ===================================================================
# apps/events/admin.py
# ===================================================================
from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    """Admin for Calendar Events"""

    list_display = ['title', 'date', 'event_type', 'school', 'created_at']
    list_filter = ['event_type', 'school', 'date']
    search_fields = ['title', 'school__school_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Evento', {
            'fields': ('school', 'title', 'date', 'event_type'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
