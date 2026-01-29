# ===================================================================
# apps/faqs/views.py - Acesso Público para Leitura COM PAGINAÇÃO
# ===================================================================
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import FAQ
from .serializers import FAQSerializer
from .pagination import FAQPagination  # ✅ PAGINAÇÃO CUSTOMIZADA
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

    Paginação Customizada:
    - Padrão: 20 itens por página
    - Opções: 15, 20 ou 25 (via ?page_size=N)
    - Outros valores não são aceitos e retornam o padrão

    Exemplos de Uso:
    ----------------
    GET /api/v1/faqs/
    → Retorna página 1 com 20 itens (padrão)

    GET /api/v1/faqs/?page=1&page_size=15
    → Retorna página 1 com 15 itens

    GET /api/v1/faqs/?page=2&page_size=25
    → Retorna página 2 com 25 itens

    GET /api/v1/faqs/?page=1&page_size=100
    → Ignora 100 (não permitido) e retorna 20 itens (padrão)

    Resposta:
    ---------
    {
        "count": 47,
        "next": "http://api.example.com/api/v1/faqs/?page=2&page_size=20",
        "previous": null,
        "results": [...]
    }
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [ReadOnlyOrSchoolStaff]
    pagination_class = FAQPagination  # ✅ PAGINAÇÃO CUSTOMIZADA APENAS PARA FAQs
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['question', 'category']
    ordering_fields = ['category', 'created_at']