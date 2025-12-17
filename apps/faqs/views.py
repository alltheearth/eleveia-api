# ===== apps/faqs/views.py =====
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import FAQ
from .serializers import FAQSerializer
from core.permissions import GestorOuOperadorPermission
from core.mixins import UsuarioEscolaMixin


class FAQViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para FAQs
    Gestor e Operador podem CRUD completo
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['pergunta', 'categoria']
    ordering_fields = ['categoria', 'criado_em']


