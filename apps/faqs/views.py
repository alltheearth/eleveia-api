# ===================================================================
# 2. apps/faqs/views.py - Acesso Público para Leitura
# ===================================================================
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import FAQ
from .serializers import FAQSerializer
from core.permissions import ReadOnlyOrSchoolStaff
from core.mixins import ReadOnlyForEndUserMixin, SchoolIsolationMixin


class FAQViewSet(
    ReadOnlyForEndUserMixin,
    SchoolIsolationMixin,
    viewsets.ModelViewSet
):
    """
    FAQs da escola.

    Permissões:
    - End Users: Apenas leitura
    - School Staff: CRUD completo
    - Isolamento total por escola
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [ReadOnlyOrSchoolStaff]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['question', 'category']
    ordering_fields = ['category', 'created_at']
