# ===================================================================
# apps/events/views.py
# ===================================================================
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import CalendarEvent
from .serializers import CalendarEventSerializer
from core.permissions import IsManagerOrOperator
from core.mixins import SchoolFilterMixin


class CalendarEventViewSet(SchoolFilterMixin, viewsets.ModelViewSet):
    """Calendar events management"""
    queryset = CalendarEvent.objects.select_related('school', 'created_by')
    serializer_class = CalendarEventSerializer
    permission_classes = [IsManagerOrOperator]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['date']

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events"""
        queryset = self.get_queryset().filter(
            date__gte=timezone.now().date()
        )[:10]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)