from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    """
    Perfil que define o tipo de acesso do usuário

    TIPOS:
    - gestor: Gerencia a escola (tudo exceto token, CNPJ, nome da escola)
    - operador: Funções administrativas (leads, contatos, eventos, FAQs)
    """
    TIPO_CHOICES = [
        ('gestor', 'Gestor da Escola'),
        ('operador', 'Operador'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    escola = models.ForeignKey(
        'Escola',
        on_delete=models.CASCADE,
        related_name='usuarios',
        help_text='Escola vinculada ao usuário'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='operador',
        help_text='Tipo de acesso do usuário'
    )
    ativo = models.BooleanField(
        default=True,
        help_text='Usuário ativo no sistema'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        indexes = [
            models.Index(fields=['escola', 'tipo']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} ({self.escola.nome_escola})"

    def is_gestor(self):
        """Verifica se é gestor"""
        return self.tipo == 'gestor'

    def is_operador(self):
        """Verifica se é operador"""
        return self.tipo == 'operador'


# ==========================================
# SERIALIZERS DE AUTENTICAÇÃO
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
