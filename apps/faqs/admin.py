# ===================================================================
# apps/faqs/admin.py
# ===================================================================
from django.contrib import admin
from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin for FAQs"""

    list_display = ['question', 'category', 'status', 'school', 'created_at']
    list_filter = ['status', 'category', 'school', 'created_at']
    search_fields = ['question', 'answer', 'category']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('FAQ', {
            'fields': ('school', 'question', 'answer', 'category', 'status'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )