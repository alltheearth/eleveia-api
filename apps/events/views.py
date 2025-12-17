from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import CalendarioEvento
from .serializers import CalendarioEventoSerializer
from core.permissions import GestorOuOperadorPermission
from core.mixins import UsuarioEscolaMixin


class CalendarioEventoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """ViewSet para Eventos"""
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