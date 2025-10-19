# eleveai/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento


# ==========================================
# SERIALIZERS DE AUTENTICAÇÃO
# ==========================================

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para visualizar dados do usuário"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class RegistroSerializer(serializers.Serializer):
    """Serializer para registro de novo usuário"""
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password2 = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

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
        return data

    def create(self, validated_data):
        """Criar novo usuário"""
        validated_data.pop('password2')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
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


# ==========================================
# SERIALIZERS DOS MODELOS
# ==========================================

class EscolaSerializer(serializers.ModelSerializer):
    """Serializer para Escola"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Escola
        fields = [
            'id', 'usuario_id', 'usuario_username', 'nome_escola', 'cnpj',
            'telefone', 'email', 'website', 'logo', 'cep', 'endereco',
            'cidade', 'estado', 'complemento', 'sobre', 'niveis_ensino',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario_id', 'usuario_username', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        """Criar escola associada ao usuário logado"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Atualizar escola (apenas o dono pode)"""
        if instance.usuario != self.context['request'].user:
            raise serializers.ValidationError("Você não tem permissão para atualizar esta escola.")
        return super().update(instance, validated_data)


class ContatoSerializer(serializers.ModelSerializer):
    """Serializer para Contato"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = Contato
        fields = [
            'id', 'usuario_id', 'escola', 'escola_nome', 'email_principal',
            'telefone_principal', 'whatsapp', 'instagram', 'facebook',
            'horario_aula', 'diretor', 'email_diretor', 'coordenador',
            'email_coordenador', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario_id', 'escola_nome', 'atualizado_em']

    def create(self, validated_data):
        """Criar contato associado ao usuário logado"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class CalendarioEventoSerializer(serializers.ModelSerializer):
    """Serializer para CalendarioEvento"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = CalendarioEvento
        fields = [
            'id', 'usuario_id', 'escola', 'escola_nome', 'data', 'evento',
            'tipo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario_id', 'escola_nome', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        """Criar evento associado ao usuário logado"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class FAQSerializer(serializers.ModelSerializer):
    """Serializer para FAQ"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = FAQ
        fields = [
            'id', 'usuario_id', 'escola', 'escola_nome', 'pergunta', 'resposta',
            'categoria', 'status', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario_id', 'escola_nome', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        """Criar FAQ associada ao usuário logado"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class DocumentoSerializer(serializers.ModelSerializer):
    """Serializer para Documento"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = Documento
        fields = [
            'id', 'usuario_id', 'escola', 'escola_nome', 'nome', 'arquivo',
            'status', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario_id', 'escola_nome', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        """Criar documento associado ao usuário logado"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer para Dashboard"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    escola_nome = serializers.CharField(source='escola.nome_escola', read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            'id', 'usuario_id', 'escola', 'escola_nome', 'status_agente',
            'interacoes_hoje', 'documentos_upload', 'faqs_criadas',
            'leads_capturados', 'taxa_resolucao', 'novos_hoje', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario_id', 'escola_nome', 'atualizado_em']