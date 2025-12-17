from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# Imports dos models
from .models import (
FAQ

)

# Imports dos serializers
from .serializers import (
    FAQSerializer
)


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
