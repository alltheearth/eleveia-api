from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import (
    FAQ
)

class FAQSerializer(serializers.ModelSerializer):
    """Serializer para FAQ"""
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = FAQ
        fields = [
            'id', 'escola', 'escola_nome', 'pergunta', 'resposta',
            'categoria', 'status', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'escola_nome', 'criado_em', 'atualizado_em']

