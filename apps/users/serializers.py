"""
Serializers para usuários e autenticação
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import PerfilUsuario


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


# ==========================================
# SERIALIZERS DE USUÁRIO
# ==========================================

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para visualizar dados do usuário"""
    perfil = PerfilUsuarioSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_superuser', 'is_staff', 'perfil'
        ]
        read_only_fields = ['id', 'is_superuser', 'is_staff']


# ==========================================
# SERIALIZERS DE AUTENTICAÇÃO
# ==========================================

class RegistroSerializer(serializers.Serializer):
    """
    Serializer para registro de novo usuário

    REGRAS:
    - Superuser pode criar sem escola (vira admin)
    - Usuário comum DEVE informar escola + tipo (gestor/operador)
    """
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password2 = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    # Campos para vincular à escola
    escola_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='ID da escola (obrigatório para não-superusers)'
    )
    tipo_perfil = serializers.ChoiceField(
        choices=['gestor', 'operador'],
        required=False,
        allow_null=True,
        help_text='Tipo de perfil: gestor ou operador'
    )

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
        """Validações gerais"""
        # Senhas devem coincidir
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})

        # Verificar se é criação por superuser
        request = self.context.get('request')
        is_superuser_creating = (
            request and
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff)
        )

        # Se NÃO for superuser criando, escola e tipo são obrigatórios
        if not is_superuser_creating:
            if not data.get('escola_id'):
                raise serializers.ValidationError({
                    "escola_id": "Escola é obrigatória para criação de usuários."
                })

            if not data.get('tipo_perfil'):
                raise serializers.ValidationError({
                    "tipo_perfil": "Tipo de perfil é obrigatório (gestor ou operador)."
                })

            # Validar se escola existe
            from apps.schools.models import Escola
            try:
                Escola.objects.get(id=data['escola_id'])
            except Escola.DoesNotExist:
                raise serializers.ValidationError({
                    "escola_id": "Escola não encontrada."
                })

        return data

    def create(self, validated_data):
        """Criar novo usuário com perfil"""
        validated_data.pop('password2')
        password = validated_data.pop('password')
        escola_id = validated_data.pop('escola_id', None)
        tipo_perfil = validated_data.pop('tipo_perfil', None)

        # Criar usuário
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Se tiver escola, criar perfil
        if escola_id and tipo_perfil:
            PerfilUsuario.objects.create(
                usuario=user,
                escola_id=escola_id,
                tipo=tipo_perfil
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