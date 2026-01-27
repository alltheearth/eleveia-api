# ===================================================================
# apps/faqs/admin.py - ENGLISH VERSION
# ===================================================================
from django.contrib import admin
from django.utils.html import format_html
from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin interface for FAQs"""

    list_display = [
        'id',
        'question_truncated',
        'category',
        'status_badge',
        'school',
        'created_at'
    ]

    list_filter = [
        'status',
        'category',
        'school',
        'created_at'
    ]

    search_fields = [
        'question',
        'answer',
        'category'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by'
    ]

    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Content', {
            'fields': (
                'school',
                'question',
                'answer',
                'category',
                'status'
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

    def question_truncated(self, obj):
        """Display truncated question"""
        if len(obj.question) > 60:
            return f"{obj.question[:60]}..."
        return obj.question

    question_truncated.short_description = 'Question'
    question_truncated.admin_order_field = 'question'

    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'active': 'green',
            'inactive': 'gray'
        }

        color = colors.get(obj.status, 'gray')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    actions = ['activate_faqs', 'deactivate_faqs']

    @admin.action(description='✅ Activate selected FAQs')
    def activate_faqs(self, request, queryset):
        """Activate selected FAQs"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} FAQ(s) activated successfully.')

    @admin.action(description='❌ Deactivate selected FAQs')
    def deactivate_faqs(self, request, queryset):
        """Deactivate selected FAQs"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} FAQ(s) deactivated successfully.')

    def save_model(self, request, obj, form, change):
        """Save creator/editor"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queries and filter by school for non-superusers"""
        qs = super().get_queryset(request)
        qs = qs.select_related('school', 'created_by')

        if not request.user.is_superuser:
            if hasattr(request.user, 'profile') and request.user.profile.school:
                qs = qs.filter(school=request.user.profile.school)

        return qs