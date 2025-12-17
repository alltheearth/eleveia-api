from rest_framework import serializers
from .models import (
   PerfilUsuario
)


# ==========================================
# SERIALIZERS DE PERFIL
# ==========================================

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para Perfil de Usuário"""
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = [
            'id', 'usuario', 'escola', 'escola_nome',
            'tipo', 'tipo_display', 'ativo',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario', 'criado_em', 'atualizado_em']
