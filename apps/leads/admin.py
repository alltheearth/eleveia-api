# ===================================================================
# apps/leads/admin.py
# ===================================================================
from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin for Leads"""

    list_display = [
        'name',
        'email',
        'telephone',
        'status',
        'origin',
        'school',
        'created_at'
    ]

    list_filter = ['status', 'origin', 'school', 'created_at']
    search_fields = ['name', 'email', 'telephone', 'observations']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Lead', {
            'fields': (
                'school',
                'name',
                'email',
                'telephone',
                'status',
                'origin',
            ),
        }),
        ('Detalhes', {
            'fields': ('observations', 'interests'),
        }),
        ('Datas', {
            'fields': ('contacted_at', 'converted_at'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
