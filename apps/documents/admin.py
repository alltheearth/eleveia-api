# ===================================================================
# apps/documents/admin.py
# ===================================================================
from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin for Documents"""

    list_display = ['name', 'status', 'school', 'created_at']
    list_filter = ['status', 'school', 'created_at']
    search_fields = ['name', 'school__school_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Documento', {
            'fields': ('school', 'name', 'file', 'status'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )