from rest_framework import serializers
from .models import Contato

class ContatoSerializer(serializers.ModelSerializer):
    """Serializer para Contatos"""
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origem_display = serializers.CharField(source='get_origem_display', read_only=True)

    class Meta:
        model = Contato
        fields = [
            'id', 'escola', 'escola_nome',
            'nome', 'email', 'telefone',
            'data_nascimento',
            'status', 'status_display',
            'origem', 'origem_display',
            'ultima_interacao', 'observacoes', 'tags',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = [
            'id', 'escola_nome',
            'status_display', 'origem_display',
            'criado_em', 'atualizado_em'
        ]