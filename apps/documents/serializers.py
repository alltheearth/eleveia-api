from rest_framework import serializers
from .models import (
    Documento
)

class DocumentoSerializer(serializers.ModelSerializer):
    """Serializer para Documento"""
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = Documento
        fields = [
            'id', 'escola', 'escola_nome', 'nome', 'arquivo',
            'status', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'escola_nome', 'criado_em', 'atualizado_em']

