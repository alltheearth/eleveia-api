# eleveai/serializers.py
from rest_framework import serializers
from .models import (
    CalendarioEvento
)

class CalendarioEventoSerializer(serializers.ModelSerializer):
    """Serializer para CalendarioEvento"""
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = CalendarioEvento
        fields = [
            'id', 'escola', 'escola_nome', 'data', 'evento',
            'tipo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'escola_nome', 'criado_em', 'atualizado_em']
