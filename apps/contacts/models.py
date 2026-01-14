# ===== apps/contacts/models.py =====
from django.db import models
from django.contrib.auth.models import User


class Contato(models.Model):
    """Modelo para armazenar contatos gerais"""
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]

    ORIGEM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('site', 'Site'),
        ('telefone', 'Telefone'),
        ('presencial', 'Presencial'),
        ('email', 'Email'),
        ('indicacao', 'Indicação'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contatos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        'schools.Escola',
        on_delete=models.CASCADE,
        related_name='contatos'
    )

    nome = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20)
    data_nascimento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='whatsapp')
    ultima_interacao = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Contato Geral'
        verbose_name_plural = 'Contatos Gerais'
        indexes = [
            models.Index(fields=['escola', 'status']),
            models.Index(fields=['criado_em']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


# ===== apps/contacts/views.py =====
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Contato
from .serializers import ContatoSerializer
from core.permissions import GestorOuOperadorPermission
from core.mixins import UsuarioEscolaMixin


class ContatoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Contatos
    Gestor e Operador podem CRUD completo
    """
    queryset = Contato.objects.all()
    serializer_class = ContatoSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'telefone', 'tags']
    ordering_fields = ['nome', 'criado_em', 'status', 'ultima_interacao']

    def get_queryset(self):
        """Aplica filtros adicionais"""
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get('status')
        origem = self.request.query_params.get('origem')

        if status_filter and status_filter != 'todos':
            queryset = queryset.filter(status=status_filter)
        if origem:
            queryset = queryset.filter(origem=origem)

        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas dos contatos"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'ativos': queryset.filter(status='ativo').count(),
            'inativos': queryset.filter(status='inativo').count(),
        }

        stats['por_origem'] = dict(
            queryset.values('origem')
            .annotate(total=Count('id'))
            .values_list('origem', 'total')
        )

        hoje = timezone.now().date()
        stats['novos_hoje'] = queryset.filter(criado_em__date=hoje).count()

        sete_dias_atras = timezone.now() - timedelta(days=7)
        stats['interacoes_recentes'] = queryset.filter(
            ultima_interacao__gte=sete_dias_atras
        ).count()

        return Response(stats)

    @action(detail=True, methods=['post'])
    def registrar_interacao(self, request, pk=None):
        """Registrar última interação"""
        contato = self.get_object()
        contato.ultima_interacao = timezone.now()
        contato.save()
        serializer = self.get_serializer(contato)
        return Response(serializer.data)


# apps/contacts/models.py
class Contato(models.Model):
    # ...

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Contato Geral'
        verbose_name_plural = 'Contatos Gerais'
        indexes = [
            models.Index(fields=['escola', 'status']),
            models.Index(fields=['criado_em']),
            models.Index(fields=['email']),
            # ✅ Adicionar índices para buscas frequentes
            models.Index(fields=['telefone']),  # Para buscar por telefone
            models.Index(fields=['escola', '-criado_em']),  # Para ordenação otimizada
        ]
        # ✅ Constraints para garantir integridade
        constraints = [
            models.CheckConstraint(
                check=models.Q(email__isnull=False) | models.Q(telefone__isnull=False),
                name='contato_must_have_email_or_phone'
            )
        ]