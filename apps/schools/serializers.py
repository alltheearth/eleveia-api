# ===================================================================
# apps/schools/serializers.py - VALIDAÇÃO ROBUSTA DE CAMPOS PROTEGIDOS
# ===================================================================
from rest_framework import serializers
from .models import School


class SchoolSerializer(serializers.ModelSerializer):
    """
    Serializer com 3 níveis de proteção:

    1. SUPER PROTECTED (apenas superuser): school_name, tax_id, messaging_token
    2. PROTECTED (superuser + manager): phone, email, address, etc
    3. PUBLIC (todos): logo, about, teaching_levels
    """

    # Campos protegidos por nível
    SUPER_PROTECTED_FIELDS = ['school_name', 'tax_id', 'messaging_token', 'application_token']
    MANAGER_EDITABLE_FIELDS = [
        'phone', 'email', 'website', 'logo',
        'postal_code', 'street_address', 'city', 'state',
        'address_complement', 'about', 'teaching_levels'
    ]

    class Meta:
        model = School
        fields = [
            'id',
            'school_name',
            'tax_id',
            'messaging_token',
            'application_token',
            'phone',
            'email',
            'website',
            'logo',
            'postal_code',
            'street_address',
            'city',
            'state',
            'address_complement',
            'about',
            'teaching_levels',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'messaging_token': {
                'write_only': True,
                'required': False,
            },
            'application_token': {
                'write_only': True,
                'required': False,
            },
        }

    def validate(self, attrs):
        """Valida campos protegidos conforme permissões"""
        request = self.context.get('request')
        instance = self.instance

        # Criação: não valida (já controlado por permissions)
        if not instance:
            return attrs

        # Atualização: verifica cada campo modificado
        if request:
            user = request.user
            is_superuser = user.is_superuser or user.is_staff
            is_manager = (
                    hasattr(user, 'profile') and
                    user.profile.is_manager() and
                    user.profile.is_active
            )

            # Verifica campos SUPER PROTECTED
            for field in self.SUPER_PROTECTED_FIELDS:
                if field in attrs:
                    current = getattr(instance, field, None)
                    new = attrs[field]

                    if current != new:
                        if not is_superuser:
                            raise serializers.ValidationError({
                                field: f"Only superusers can modify '{field}'. "
                                       f"Current user role: {user.profile.role if hasattr(user, 'profile') else 'none'}"
                            })

            # Verifica campos MANAGER EDITABLE
            for field in self.MANAGER_EDITABLE_FIELDS:
                if field in attrs:
                    if not (is_superuser or is_manager):
                        raise serializers.ValidationError({
                            field: f"Only superusers or managers can modify '{field}'."
                        })

        return attrs

    def to_representation(self, instance):
        """Oculta campos sensíveis conforme permissões"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request:
            user = request.user
            is_superuser = user.is_superuser or user.is_staff

            # Oculta messaging_token de não-superusers
            if not is_superuser:
                data.pop('messaging_token', None)

        return data


class SchoolPublicSerializer(serializers.ModelSerializer):
    """
    Serializer público para End Users.
    Expõe apenas informações não-sensíveis.
    """

    class Meta:
        model = School
        fields = [
            'id',
            'school_name',
            'phone',
            'email',
            'website',
            'logo',
            'city',
            'state',
            'about',
            'teaching_levels',
        ]
        read_only_fields = fields  # Tudo read-only para end users