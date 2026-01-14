# ===================================================================
# apps/schools/views.py
# ===================================================================
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import School
from .serializers import SchoolSerializer
from core.permissions import IsSchoolOwnerOrReadOnly


class SchoolViewSet(viewsets.ModelViewSet):
    """
    School management endpoint.

    Permissions:
    - CREATE: Only superuser
    - READ: Superuser (all) or users from that school
    - UPDATE: Superuser (all fields) or Manager (non-protected fields)
    - DELETE: Only superuser
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSchoolOwnerOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['school_name', 'city', 'state']
    ordering_fields = ['school_name', 'created_at']

    def get_queryset(self):
        """Filter schools based on user permissions"""
        queryset = super().get_queryset()

        # Superusers see all schools
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset

        # Regular users see only their school
        if hasattr(self.request.user, 'profile'):
            return queryset.filter(id=self.request.user.profile.school_id)

        return queryset.none()
