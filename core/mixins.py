"""
core/mixins.py
Refactored mixins with English naming
"""


class SchoolFilterMixin:
    """
    Mixin for ViewSets that need to filter by user's school.

    Behavior:
    - Superuser: sees everything
    - Regular user: sees only their school's data
    """

    def get_queryset(self):
        """Filter queryset by user's school"""
        queryset = super().get_queryset()

        # Superusers see everything
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        # Regular users see only their school's data
        if hasattr(self.request.user, 'profile'):
            return queryset.filter(school=self.request.user.profile.school)

        # No profile = no access
        return queryset.none()

    def perform_create(self, serializer):
        """Automatically link to user's school on creation"""
        if hasattr(self.request.user, 'profile'):
            serializer.save(
                created_by=self.request.user,
                school=self.request.user.profile.school
            )
        else:
            serializer.save(created_by=self.request.user)


class TimestampMixin:
    """
    Mixin for models with automatic timestamps.
    Note: This is rarely needed as Django handles this with auto_now/auto_now_add
    """

    def save(self, *args, **kwargs):
        """Hook for additional save logic"""
        super().save(*args, **kwargs)