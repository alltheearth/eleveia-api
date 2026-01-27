# ===================================================================
# apps/events/admin.py - FIXED
# ===================================================================
from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    """Admin for Calendar Events"""

    list_display = [
        'id',
        'title',
        'start_date',
        'end_date',
        'duration_days',
        'event_type',
        'school',
        'created_by',
        'created_at'
    ]

    list_filter = [
        'event_type',
        'school',
        'start_date',
        'end_date'
    ]

    search_fields = [
        'title',
        'description',
        'school__school_name'
    ]

    readonly_fields = [
        'id',
        'duration_days',
        'is_single_day',
        'created_at',
        'updated_at'
    ]

    date_hierarchy = 'start_date'

    ordering = ['-start_date']

    fieldsets = (
        ('Event Information', {
            'fields': (
                'school',
                'title',
                'description',
                'event_type'
            ),
        }),
        ('Date Range', {
            'fields': (
                'start_date',
                'end_date',
                'duration_days',
                'is_single_day'
            ),
        }),
        ('Metadata', {
            'fields': (
                'id',
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make created_by readonly when editing"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Editing existing object
            readonly.append('created_by')
        return readonly

    def save_model(self, request, obj, form, change):
        """Set created_by on creation"""
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)