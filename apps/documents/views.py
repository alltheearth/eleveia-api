# ===================================================================
# apps/documents/views.py - CORRIGIDO
# ===================================================================
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document
from .serializers import DocumentSerializer
from core.permissions import IsSchoolStaff  # ✅ CORRIGIDO: era IsManagerOrOperator
from core.mixins import SchoolIsolationMixin


class DocumentViewSet(SchoolIsolationMixin, viewsets.ModelViewSet):
    """Document management"""
    queryset = Document.objects.select_related('school', 'created_by')
    serializer_class = DocumentSerializer
    permission_classes = [IsSchoolStaff]  # ✅ CORRIGIDO

    @action(detail=False, methods=['get'])
    def unprocessed(self, request):
        """Get unprocessed documents"""
        queryset = self.get_queryset().filter(status__in=['pending', 'error'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)