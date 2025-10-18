# eleveai/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para visualizar dados do usuário"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar dados do usuário"""

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


class RegistroSerializer(serializers.ModelSerializer):
    """Serializer para registro de novo usuário"""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': False},
        }

    def validate_username(self, value):
        """Validar se username já existe"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def validate_email(self, value):
        """Validar se email já existe"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está cadastrado.")
        return value

    def validate(self, data):
        """Validar se as senhas conferem"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        if len(data['password']) < 8:
            raise serializers.ValidationError({"password": "A senha deve ter pelo menos 8 caracteres."})
        return data

    def create(self, validated_data):
        """Criar novo usuário e gerar token"""
        validated_data.pop('password2')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Token é criado automaticamente pelo signal
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """Autenticar usuário"""
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("Username e password são obrigatórios.")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Username ou password incorretos.")

        data['user'] = user
        return data


class MudarSenhaSerializer(serializers.Serializer):
    """Serializer para mudar senha"""
    senha_atual = serializers.CharField(write_only=True, required=True)
    senha_nova = serializers.CharField(write_only=True, required=True, min_length=8)
    senha_nova_confirmacao = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, data):
        if data['senha_nova'] != data['senha_nova_confirmacao']:
            raise serializers.ValidationError({"senha_nova": "As senhas não coincidem."})
        return data


class AuthResponseSerializer(serializers.Serializer):
    """Serializer para resposta de autenticação"""
    token = serializers.CharField()
    user = UsuarioSerializer()
    message = serializers.CharField()


# Serializers dos modelos
class EscolaSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Escola
        fields = [
            'id', 'usuario_id', 'nome_escola', 'cnpj', 'telefone', 'email',
            'website', 'logo', 'cep', 'endereco', 'cidade', 'estado', 'complemento',
            'sobre', 'niveis_ensino', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['usuario_id', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class ContatoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Contato
        fields = [
            'id', 'usuario_id', 'escola', 'email_principal', 'telefone_principal',
            'whatsapp', 'instagram', 'facebook', 'horario_aula', 'diretor',
            'email_diretor', 'coordenador', 'email_coordenador', 'atualizado_em'
        ]
        read_only_fields = ['usuario_id', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class CalendarioEventoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = CalendarioEvento
        fields = ['id', 'usuario_id', 'escola', 'data', 'evento', 'tipo', 'criado_em', 'atualizado_em']
        read_only_fields = ['usuario_id', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class FAQSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = FAQ
        fields = ['id', 'usuario_id', 'escola', 'pergunta', 'resposta', 'categoria', 'status', 'criado_em',
                  'atualizado_em']
        read_only_fields = ['usuario_id', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class DocumentoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Documento
        fields = ['id', 'usuario_id', 'escola', 'nome', 'arquivo', 'status', 'criado_em', 'atualizado_em']
        read_only_fields = ['usuario_id', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class DashboardSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            'id', 'usuario_id', 'escola', 'status_agente', 'interacoes_hoje',
            'documentos_upload', 'faqs_criadas', 'leads_capturados', 'taxa_resolucao',
            'novos_hoje', 'atualizado_em'
        ]
        read_only_fields = ['usuario_id', 'atualizado_em']