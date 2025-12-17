# ===== apps/events/models.py =====
from django.db import models
from django.contrib.auth.models import User


class CalendarioEvento(models.Model):
    """Modelo para armazenar eventos do calendário escolar"""
    TIPO_CHOICES = [
        ('feriado', '📌 Feriado'),
        ('prova', '📝 Prova/Avaliação'),
        ('formatura', '🎓 Formatura'),
        ('evento_cultural', '🎉 Evento Cultural'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='eventos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        'schools.Escola',
        on_delete=models.CASCADE,
        related_name='eventos'
    )

    data = models.DateField()
    evento = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['data']
        verbose_name = 'Evento do Calendário'
        verbose_name_plural = 'Eventos do Calendário'

    def __str__(self):
        return f"{self.evento} - {self.data}"


# ===== apps/events/views.py =====
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


