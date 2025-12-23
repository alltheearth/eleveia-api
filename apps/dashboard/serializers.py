# apps/dashboard/serializers.py
from rest_framework import serializers
from .models import DashboardMetrics, InteracaoN8N


class DashboardMetricsSerializer(serializers.ModelSerializer):
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = DashboardMetrics
        fields = [
            'id', 'escola', 'escola_nome',
            'total_interacoes', 'interacoes_hoje',
            'leads_capturados', 'tickets_abertos',
            'tempo_medio_resposta', 'taxa_satisfacao', 'taxa_conversao',
            'status_agente',
            'n8n_workflow_id', 'n8n_execution_id',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class InteracaoN8NSerializer(serializers.ModelSerializer):
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = InteracaoN8N
        fields = [
            'id', 'escola', 'escola_nome',
            'tipo', 'titulo', 'descricao', 'dados',
            'n8n_workflow_id', 'n8n_execution_id',
            'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


# Serializer para webhook do n8n
class N8NWebhookSerializer(serializers.Serializer):
    """Serializer para receber dados do n8n via webhook"""

    # Identificação da escola
    escola_id = serializers.IntegerField(required=True)

    # Tipo de evento
    evento = serializers.ChoiceField(
        choices=['metrics_update', 'nova_interacao'],
        required=True
    )

    # Dados do evento
    dados = serializers.JSONField(required=True)

    # Metadados do n8n
    workflow_id = serializers.CharField(required=False, allow_blank=True)
    execution_id = serializers.CharField(required=False, allow_blank=True)

