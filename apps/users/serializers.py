# ===================================================================
# apps/users/serializers.py - VERSÃO CORRIGIDA COM VALIDAÇÃO ROBUSTA
# ===================================================================
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer com validação de escola obrigatória
    para não-superusers
    """
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'school',
            'school_name',
            'role',
            'role_display',
            'is_active',
            'phone',
            'date_of_birth',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        """
        ✅ VALIDAÇÃO CRÍTICA: Garante que não-superusers tenham escola

        Esta validação complementa a do model.clean() e garante que
        a regra de negócio seja respeitada mesmo via API.
        """
        # Pega o usuário (pode vir de attrs ou da instância em updates)
        user = attrs.get('user')
        if not user and self.instance:
            user = self.instance.user

        # Pega a escola (pode vir de attrs ou da instância)
        school = attrs.get('school')
        if school is None and self.instance:
            school = self.instance.school

        # Validação: Não-superusers DEVEM ter escola
        if user and not (user.is_superuser or user.is_staff):
            if not school:
                raise serializers.ValidationError({
                    'school': 'Non-superuser profiles must have a school assigned. '
                              'Only superusers can have school=null.'
                })

        return attrs

    def validate_role(self, value):
        """Valida o role fornecido"""
        valid_roles = ['manager', 'operator', 'end_user']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value


class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile"""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_superuser',
            'is_staff',
            'profile',
        ]
        read_only_fields = ['id', 'is_superuser', 'is_staff']


class RegisterSerializer(serializers.Serializer):
    """
    User registration serializer com validação de escola obrigatória
    para não-superusers
    """
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password2 = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    school_id = serializers.IntegerField(required=False, allow_null=True)
    role = serializers.ChoiceField(
        choices=['manager', 'operator', 'end_user'],
        required=False,
        allow_null=True
    )

    def validate_username(self, value):
        """Valida se username já existe"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        """Valida se email já existe"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate(self, data):
        """
        ✅ VALIDAÇÃO PRINCIPAL DO REGISTRO

        Regras:
        1. Senhas devem coincidir
        2. Superusers registrando: podem omitir escola e role
        3. Não-superusers registrando: DEVEM fornecer escola e role
        """
        # 1. Valida senhas
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                "password": "Passwords don't match"
            })

        # 2. Verifica quem está fazendo o registro
        request = self.context.get('request')
        is_superuser_registering = (
                request and
                request.user and
                request.user.is_authenticated and
                (request.user.is_superuser or request.user.is_staff)
        )

        # 3. ✅ REGRA CRÍTICA: Não-superusers DEVEM fornecer escola e role
        if not is_superuser_registering:
            if not data.get('school_id'):
                raise serializers.ValidationError({
                    "school_id": "School is required for non-superuser registration. "
                                 "Only superusers can create users without a school."
                })
            if not data.get('role'):
                raise serializers.ValidationError({
                    "role": "Role is required (manager, operator, or end_user)"
                })

        return data

    def create(self, validated_data):
        """
        Cria usuário e perfil associado

        ✅ Garante que a escola seja vinculada corretamente
        """
        # Remove campos extras
        validated_data.pop('password2')
        password = validated_data.pop('password')
        school_id = validated_data.pop('school_id', None)
        role = validated_data.pop('role', None)

        # Cria usuário
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # ✅ Cria perfil COM escola para não-superusers
        if school_id and role:
            UserProfile.objects.create(
                user=user,
                school_id=school_id,
                role=role
            )
        elif user.is_superuser or user.is_staff:
            # Superuser criado manualmente pode não ter perfil inicialmente
            # O signal create_superuser_profile cuida disso
            pass
        else:
            # Não deveria chegar aqui por causa da validação,
            # mas é um safety check
            raise serializers.ValidationError(
                "Non-superuser must have school and role"
            )

        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Valida credenciais e retorna usuário autenticado
        """
        user = authenticate(
            username=data.get('username'),
            password=data.get('password')
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # Verifica se usuário está ativo
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        # ✅ VALIDAÇÃO EXTRA: Verifica se perfil está ativo
        if hasattr(user, 'profile'):
            if not user.profile.is_active:
                raise serializers.ValidationError("User profile is inactive")

        data['user'] = user
        return data


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de perfil do usuário

    Permite atualização apenas de campos não-críticos
    """

    class Meta:
        model = UserProfile
        fields = [
            'phone',
            'date_of_birth',
        ]

    def validate(self, attrs):
        """
        Não permite mudança de escola ou role via este serializer
        (isso deve ser feito por managers/superusers via admin ou ViewSet específico)
        """
        if 'school' in attrs:
            raise serializers.ValidationError({
                'school': 'Cannot change school via profile update. '
                          'Contact your administrator.'
            })

        if 'role' in attrs:
            raise serializers.ValidationError({
                'role': 'Cannot change role via profile update. '
                        'Contact your administrator.'
            })

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para mudança de senha"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password2 = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate_old_password(self, value):
        """Valida se senha antiga está correta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate(self, data):
        """Valida se novas senhas coincidem"""
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({
                "new_password": "New passwords don't match"
            })
        return data

    def save(self):
        """Atualiza a senha do usuário"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user