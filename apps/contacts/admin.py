# ===================================================================
# apps/contacts/admin.py
# ===================================================================
from django.contrib import admin
from django.utils.html import format_html
from .models import WhatsAppContact


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    """Admin for WhatsApp Contacts"""

    list_display = [
        'id',
        'full_name',
        'phone',
        'email',
        'school',
        'status_badge',
        'source',
        'last_interaction_at',
        'created_at',
    ]

    list_filter = [
        'status',
        'source',
        'school',
        'created_at',
        'last_interaction_at',
    ]

    search_fields = [
        'full_name',
        'email',
        'phone',
        'tags',
        'notes',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('school', 'created_by'),
        }),
        ('Dados do Contato', {
            'fields': (
                'full_name',
                'email',
                'phone',
                'date_of_birth',
            ),
        }),
        ('Status e Origem', {
            'fields': ('status', 'source'),
        }),
        ('Interações', {
            'fields': ('last_interaction_at', 'notes', 'tags'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'active': 'green',
            'inactive': 'red',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    actions = ['mark_as_active', 'mark_as_inactive']

    def mark_as_active(self, request, queryset):
        """Mark selected contacts as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} contatos marcados como ativos.')

    mark_as_active.short_description = 'Marcar como ativo'

    def mark_as_inactive(self, request, queryset):
        """Mark selected contacts as inactive"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} contatos marcados como inativos.')

    mark_as_inactive.short_description = 'Marcar como inativo'