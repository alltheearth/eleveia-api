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
    CalendarioEvento
)

# Imports dos serializers
from .serializers import (
    CalendarioEventoSerializer,
)



class CalendarioEventoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Eventos
    Gestor e Operador podem CRUD completo
    """
    queryset = CalendarioEvento.objects.all()
    serializer_class = CalendarioEventoSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['evento']
    ordering_fields = ['data']

    @action(detail=False, methods=['get'])
    def proximos_eventos(self, request):
        """Retorna próximos eventos"""
        queryset = self.get_queryset().filter(
            data__gte=timezone.now().date()
        )[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
