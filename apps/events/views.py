# apps/events/views.py - UPDATED WITH FILTERING
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from .models import CalendarEvent
from .serializers import CalendarEventSerializer
from core.permissions import ReadOnlyOrSchoolStaff
from core.mixins import ReadOnlyForEndUserMixin, SchoolIsolationMixin


class CalendarEventViewSet(
    ReadOnlyForEndUserMixin,
    SchoolIsolationMixin,
    viewsets.ModelViewSet
):
    """
    Calendar Events Management

    Permissions:
    - End Users: Read-only
    - School Staff: Full CRUD

    Filters:
    - event_type: Filter by type (holiday, exam, graduation, cultural)
    - start_date: Filter events starting from this date
    - end_date: Filter events ending before this date
    - search: Search in title and description
    """
    queryset = CalendarEvent.objects.select_related('school', 'created_by')
    serializer_class = CalendarEventSerializer
    permission_classes = [ReadOnlyOrSchoolStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['start_date']
    filterset_fields = ['event_type']

    def get_queryset(self):
        """
        Filter queryset by query parameters

        Query params:
        - event_type: holiday, exam, graduation, cultural
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        - search: text search
        """
        queryset = super().get_queryset()

        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type and event_type != 'all':
            queryset = queryset.filter(event_type=event_type)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(end_date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__lte=end)
            except ValueError:
                pass

        return queryset

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events (starting from today)"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            end_date__gte=today
        )[:10]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get event statistics"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'by_type': {
                'holiday': queryset.filter(event_type='holiday').count(),
                'exam': queryset.filter(event_type='exam').count(),
                'graduation': queryset.filter(event_type='graduation').count(),
                'cultural': queryset.filter(event_type='cultural').count(),
            },
            'upcoming': queryset.filter(
                end_date__gte=timezone.now().date()
            ).count(),
        }

        return Response(stats)