# apps/schools/validators.py
from rest_framework import serializers


class ProtectedFieldsValidator:
    """Validador para campos protegidos da escola"""

    def __init__(self, protected_fields):
        self.protected_fields = protected_fields

    def __call__(self, data, serializer):
        """Validar se usuário pode alterar campos protegidos"""
        if not serializer.instance:
            return  # Criação não precisa validar

        request = serializer.context.get('request')

        if request and not (request.user.is_superuser or request.user.is_staff):
            for field in self.protected_fields:
                if field in data:
                    valor_atual = getattr(serializer.instance, field)
                    valor_novo = data[field]

                    if valor_atual != valor_novo:
                        raise serializers.ValidationError({
                            field: f"Apenas superusuários podem alterar {field}"
                        })


# apps/schools/serializers.py
class EscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = [...]
        validators = [
            ProtectedFieldsValidator(['nome_escola', 'cnpj', 'token_mensagens'])
        ]