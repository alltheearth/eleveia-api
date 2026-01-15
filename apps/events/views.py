# ===================================================================
# 3. apps/events/views.py - Eventos com Acesso Público
# ===================================================================
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

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
    Eventos do calendário escolar.

    Permissões:
    - End Users: Apenas leitura
    - School Staff: CRUD completo
    """
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [ReadOnlyOrSchoolStaff]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['date', 'created_at']

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Próximos eventos (público)"""
        queryset = self.get_queryset().filter(
            date__gte=timezone.now().date()
        )[:10]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)