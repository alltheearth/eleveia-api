# apps/dashboard/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta

from .models import DashboardMetrics, InteracaoN8N
from .serializers import (
    DashboardMetricsSerializer,
    InteracaoN8NSerializer,
    N8NWebhookSerializer
)
from core.permissions import GestorOuOperadorPermission
from core.mixins import UsuarioEscolaMixin


class DashboardMetricsViewSet(UsuarioEscolaMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para métricas do dashboard
    Apenas leitura - dados vêm do n8n
    """
    queryset = DashboardMetrics.objects.all()
    serializer_class = DashboardMetricsSerializer
    permission_classes = [GestorOuOperadorPermission]

    def get_queryset(self):
        """Retorna métricas da escola do usuário"""
        queryset = super().get_queryset()

        # Pegar apenas as métricas mais recentes
        return queryset.order_by('-atualizado_em')[:1]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retorna métricas atuais da escola"""
        queryset = self.get_queryset()

        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)

        # Se não há métricas, retornar valores zerados
        return Response({
            'total_interacoes': 0,
            'interacoes_hoje': 0,
            'leads_capturados': 0,
            'tickets_abertos': 0,
            'tempo_medio_resposta': '0min',
            'taxa_satisfacao': 0,
            'taxa_conversao': 0,
            'status_agente': 'offline',
        })


class InteracaoN8NViewSet(UsuarioEscolaMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para interações do n8n
    Apenas leitura
    """
    queryset = InteracaoN8N.objects.all()
    serializer_class = InteracaoN8NSerializer
    permission_classes = [GestorOuOperadorPermission]

    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retorna interações recentes (últimas 24h)"""
        hoje = timezone.now()
        ontem = hoje - timedelta(days=1)

        queryset = self.get_queryset().filter(
            criado_em__gte=ontem
        )[:20]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================
# WEBHOOK ENDPOINT PARA N8N
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])  # ⚠️ Proteger com token/secret em produção
def n8n_webhook(request):
    """
    Endpoint para receber dados do n8n

    POST /api/v1/dashboard/webhook/n8n/

    Body exemplo:
    {
        "escola_id": 1,
        "evento": "metrics_update",
        "dados": {
            "total_interacoes": 234,
            "interacoes_hoje": 12,
            "leads_capturados": 45,
            "tickets_abertos": 8,
            "tempo_medio_resposta": "5min",
            "taxa_satisfacao": 92.5,
            "taxa_conversao": 15.8,
            "status_agente": "online"
        },
        "workflow_id": "workflow_123",
        "execution_id": "exec_456"
    }
    """

    # ✅ TODO: Validar secret token do n8n
    # secret = request.headers.get('X-N8N-Secret')
    # if secret != settings.N8N_WEBHOOK_SECRET:
    #     return Response({'error': 'Unauthorized'}, status=401)

    serializer = N8NWebhookSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data
    escola_id = data['escola_id']
    evento = data['evento']
    dados = data['dados']

    try:
        from apps.schools.models import Escola
        escola = Escola.objects.get(id=escola_id)

        # ============================================
        # PROCESSAR EVENTO
        # ============================================

        if evento == 'metrics_update':
            # Atualizar ou criar métricas
            metrics, created = DashboardMetrics.objects.update_or_create(
                escola=escola,
                defaults={
                    'total_interacoes': dados.get('total_interacoes', 0),
                    'interacoes_hoje': dados.get('interacoes_hoje', 0),
                    'leads_capturados': dados.get('leads_capturados', 0),
                    'tickets_abertos': dados.get('tickets_abertos', 0),
                    'tempo_medio_resposta': dados.get('tempo_medio_resposta', '0min'),
                    'taxa_satisfacao': dados.get('taxa_satisfacao', 0),
                    'taxa_conversao': dados.get('taxa_conversao', 0),
                    'status_agente': dados.get('status_agente', 'online'),
                    'n8n_workflow_id': data.get('workflow_id', ''),
                    'n8n_execution_id': data.get('execution_id', ''),
                }
            )

            return Response({
                'success': True,
                'message': 'Métricas atualizadas' if not created else 'Métricas criadas',
                'metrics_id': metrics.id
            }, status=status.HTTP_200_OK)

        elif evento == 'nova_interacao':
            # Criar nova interação
            interacao = InteracaoN8N.objects.create(
                escola=escola,
                tipo=dados.get('tipo', 'mensagem'),
                titulo=dados.get('titulo', ''),
                descricao=dados.get('descricao', ''),
                dados=dados,
                n8n_workflow_id=data.get('workflow_id', ''),
                n8n_execution_id=data.get('execution_id', ''),
            )

            return Response({
                'success': True,
                'message': 'Interação registrada',
                'interacao_id': interacao.id
            }, status=status.HTTP_201_CREATED)

        else:
            return Response(
                {'error': f'Evento desconhecido: {evento}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Escola.DoesNotExist:
        return Response(
            {'error': f'Escola {escola_id} não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {'error': 'Erro ao processar webhook', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
