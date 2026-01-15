"""
core/permissions.py
Refactored permissions with clear naming and better structure
"""
from rest_framework import permissions


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """
    Only superusers can create/update/delete.
    Everyone else can only read.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow read-only for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only superusers can write
        return request.user.is_superuser or request.user.is_staff


class IsSchoolOwnerOrReadOnly(permissions.BasePermission):
    """
    School Permissions:
    - CREATE: Only superuser
    - READ: Superuser (all schools) or users linked to that school
    - UPDATE: Superuser (all fields) or Manager (non-protected fields only)
    - DELETE: Only superuser
    """

    def has_permission(self, request, view):
        """Check basic permission to access schools endpoint"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Only superusers can create schools
        if request.method == 'POST':
            return False

        # Must have a profile to access schools
        return hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        """Check permission on a specific school object"""
        # Superusers can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True

        # User must have a profile
        if not hasattr(request.user, 'profile'):
            return False

        profile = request.user.profile

        # User can only access their own school
        if profile.school != obj:
            return False

        # Read access for everyone in the school
        if request.method in permissions.SAFE_METHODS:
            return True

        # Delete only for superuser (already handled above)
        if request.method == 'DELETE':
            return False

        # Update only for managers
        if request.method in ['PUT', 'PATCH']:
            return profile.is_manager() and profile.is_active

        return False


class IsManagerOrOperator(permissions.BasePermission):
    """
    Day-to-day operations permission.
    Both managers and operators can CRUD resources in their school.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have full access
        if request.user.is_superuser or request.user.is_staff:
            return True

        # User must have an active profile
        return (
            hasattr(request.user, 'profile') and
            request.user.profile.is_active
        )

    def has_object_permission(self, request, view, obj):
        """Check permission on specific object"""
        # Superusers have full access
        if request.user.is_superuser or request.user.is_staff:
            return True

        # User must have a profile
        if not hasattr(request.user, 'profile'):
            return False

        profile = request.user.profile

        # Check if object belongs to user's school
        if hasattr(obj, 'school') and profile.school != obj.school:
            return False

        # Must be active
        return profile.is_active


class IsManagerOnly(permissions.BasePermission):
    """
    Only managers (or superusers) can access.
    Used for sensitive operations like managing users, school settings, etc.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have full access
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Must be an active manager
        return (
            hasattr(request.user, 'profile') and
            request.user.profile.is_manager() and
            request.user.profile.is_active
        )

    def has_object_permission(self, request, view, obj):
        """Check permission on specific object"""
        # Superusers have full access
        if request.user.is_superuser or request.user.is_staff:
            return True

        # User must have a profile
        if not hasattr(request.user, 'profile'):
            return False

        profile = request.user.profile

        # Check if object belongs to user's school
        if hasattr(obj, 'school') and profile.school != obj.school:
            return False

        # Must be an active manager
        return profile.is_manager() and profile.is_active


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object owner can edit, others can only read.
    Useful for user profiles, personal data, etc.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusers can edit anything
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Object must have an 'created_by' or 'user' field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False