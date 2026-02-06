# ===================================================================
# apps/schools/admin.py
# ===================================================================
from django.contrib import admin
from django.utils.html import format_html
from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """Admin interface for School model"""

    list_display = [
        'id',
        'school_name',
        'city',
        'state',
        'phone',
        'email',
        'display_logo',
        'created_at',
    ]

    list_filter = [
        'state',
        'city',
        'created_at',
    ]

    search_fields = [
        'school_name',
        'tax_id',
        'email',
        'city',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'display_logo',
    ]

    fieldsets = (
        ('Informações Protegidas (Superuser Only)', {
            'fields': ('school_name', 'tax_id', 'messaging_token', 'application_token'),
            'description': 'Apenas superusuários podem modificar estes campos'
        }),
        ('Contato', {
            'fields': ('phone', 'email', 'website'),
        }),
        ('Endereço', {
            'fields': (
                'postal_code',
                'street_address',
                'city',
                'state',
                'address_complement',
            ),
        }),
        ('Informações Adicionais', {
            'fields': ('about', 'teaching_levels', 'logo'),
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def display_logo(self, obj):
        """Display logo thumbnail"""
        if obj.logo:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.logo.url
            )
        return "Sem logo"

    display_logo.short_description = 'Logo'

    def get_readonly_fields(self, request, obj=None):
        """Only superusers can edit protected fields"""
        readonly = list(super().get_readonly_fields(request, obj))

        if obj and not request.user.is_superuser:
            readonly.extend(['school_name', 'tax_id', 'messaging_token', 'application_token'])

        return readonly

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete schools"""
        return request.user.is_superuser