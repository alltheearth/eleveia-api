# eleveai/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import (
    Escola
)

class EscolaSerializer(serializers.ModelSerializer):
    """
    Serializer para Escola

    CAMPOS PROTEGIDOS (só superuser pode alterar):
    - nome_escola
    - cnpj
    - token_mensagens
    """

    class Meta:
        model = Escola
        fields = [
            'id', 'nome_escola', 'cnpj', 'telefone', 'email', 'website', 'logo',
            'cep', 'endereco', 'cidade', 'estado', 'complemento',
            'sobre', 'niveis_ensino', 'token_mensagens',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']

    def validate(self, data):
        """Validar campos protegidos"""
        request = self.context.get('request')

        # Se for update e NÃO for superuser, bloquear campos protegidos
        if self.instance and request:
            is_superuser = (
                    request.user.is_superuser or
                    request.user.is_staff
            )

            if not is_superuser:
                campos_protegidos = ['nome_escola', 'cnpj', 'token_mensagens']

                for campo in campos_protegidos:
                    if campo in data:
                        # Verificar se tentou alterar
                        valor_atual = getattr(self.instance, campo)
                        valor_novo = data[campo]

                        if valor_atual != valor_novo:
                            raise serializers.ValidationError({
                                campo: f"Apenas superusuários podem alterar {campo}"
                            })

        return data