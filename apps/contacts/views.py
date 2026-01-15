# ===================================================================
# apps/contacts/views.py - CORRIGIDO
# ===================================================================
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import WhatsAppContact
from .serializers import WhatsAppContactSerializer
from core.permissions import IsSchoolStaff  # ✅ CORRIGIDO: era IsManagerOrOperator
from core.mixins import SchoolIsolationMixin


class WhatsAppContactViewSet(SchoolIsolationMixin, viewsets.ModelViewSet):
    """WhatsApp contacts management"""
    queryset = WhatsAppContact.objects.select_related('school', 'created_by')
    serializer_class = WhatsAppContactSerializer
    permission_classes = [IsSchoolStaff]  # ✅ CORRIGIDO
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['full_name', 'email', 'phone', 'tags']
    ordering_fields = ['full_name', 'created_at', 'status', 'last_interaction_at']

    def get_queryset(self):
        """Apply additional filters"""
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get('status')
        source = self.request.query_params.get('source')

        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        if source:
            queryset = queryset.filter(source=source)

        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get contact statistics"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'active': queryset.filter(status='active').count(),
            'inactive': queryset.filter(status='inactive').count(),
        }

        stats['by_source'] = dict(
            queryset.values('source')
            .annotate(total=Count('id'))
            .values_list('source', 'total')
        )

        today = timezone.now().date()
        stats['new_today'] = queryset.filter(created_at__date=today).count()

        week_ago = timezone.now() - timedelta(days=7)
        stats['recent_interactions'] = queryset.filter(
            last_interaction_at__gte=week_ago
        ).count()

        return Response(stats)

    @action(detail=True, methods=['post'])
    def record_interaction(self, request, pk=None):
        """Record last interaction timestamp"""
        contact = self.get_object()
        contact.last_interaction_at = timezone.now()
        contact.save(update_fields=['last_interaction_at', 'updated_at'])

        serializer = self.get_serializer(contact)
        return Response(serializer.data)