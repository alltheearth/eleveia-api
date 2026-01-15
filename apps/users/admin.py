# ===================================================================
# apps/users/admin.py
# ===================================================================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'

    fields = [
        'school',
        'role',
        'is_active',
        'created_at',
        'updated_at',
    ]

    readonly_fields = ['created_at', 'updated_at']


class CustomUserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline"""
    inlines = [UserProfileInline]

    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'get_school',
        'get_role',
        'is_active',
        'is_staff',
    ]

    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'profile__role',
        'profile__school',
    ]

    def get_school(self, obj):
        """Get user's school"""
        return obj.profile.school.school_name if hasattr(obj, 'profile') else '-'

    get_school.short_description = 'Escola'
    get_school.admin_order_field = 'profile__school__school_name'

    def get_role(self, obj):
        """Get user's role"""
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'

    get_role.short_description = 'Tipo'
    get_role.admin_order_field = 'profile__role'


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile (standalone)"""

    list_display = [
        'id',
        'user',
        'school',
        'role',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'role',
        'is_active',
        'school',
        'created_at',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'school__school_name',
    ]

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Vínculo', {
            'fields': ('user', 'school'),
        }),
        ('Permissões', {
            'fields': ('role', 'is_active'),
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )