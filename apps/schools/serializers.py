# ===================================================================
# apps/schools/serializers.py
# ===================================================================
from rest_framework import serializers
from .models import School


class SchoolSerializer(serializers.ModelSerializer):
    """School serializer with protected fields validation"""

    class Meta:
        model = School
        fields = [
            'id',
            'school_name',
            'tax_id',
            'messaging_token',
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
        }

    def validate(self, attrs):
        """Validate protected fields - only superusers can modify"""
        request = self.context.get('request')
        instance = self.instance

        if instance and request:
            # Non-superusers cannot modify protected fields
            if not (request.user.is_superuser or request.user.is_staff):
                for field in instance.protected_fields:
                    if field in attrs:
                        current = getattr(instance, field)
                        new = attrs[field]

                        if current != new:
                            raise serializers.ValidationError({
                                field: f"Only superusers can modify '{field}'"
                            })

        return attrs

    def to_representation(self, instance):
        """Hide messaging_token from non-superusers"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and not (request.user.is_superuser or request.user.is_staff):
            data.pop('messaging_token', None)

        return data
