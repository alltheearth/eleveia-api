# ===================================================================
# apps/faqs/views.py
# ===================================================================
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import FAQ
from .serializers import FAQSerializer
from core.permissions import IsManagerOrOperator
from core.mixins import SchoolFilterMixin


class FAQViewSet(SchoolFilterMixin, viewsets.ModelViewSet):
    """FAQ management"""
    queryset = FAQ.objects.select_related('school', 'created_by')
    serializer_class = FAQSerializer
    permission_classes = [IsManagerOrOperator]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['question', 'category']
    ordering_fields = ['category', 'created_at']
