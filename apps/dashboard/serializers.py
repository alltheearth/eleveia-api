from rest_framework import serializers

from .models import (
    Dashboard
)

class DashboardSerializer(serializers.ModelSerializer):
    """Serializer para Dashboard"""
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            'id', 'escola', 'escola_nome', 'status_agente',
            'interacoes_hoje', 'documentos_upload', 'faqs_criadas',
            'leads_capturados', 'taxa_resolucao', 'novos_hoje', 'atualizado_em'
        ]
        read_only_fields = ['id', 'escola_nome', 'atualizado_em']

