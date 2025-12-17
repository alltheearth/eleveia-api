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
Contato
)

# Imports dos serializers
from .serializers import (
     ContatoSerializer
)

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