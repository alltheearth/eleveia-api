
from rest_framework import serializers
from .models import (
    Lead
)

class LeadSerializer(serializers.ModelSerializer):
    """Serializer para Lead"""

    class Meta:
        model = Lead
        fields = [
            'id', 'school',
            'name', 'email', 'telephone',
            'status',
            'origin',
            'observations', 'interests',
            'contacted_at', 'converted_at',
            'created_at', 'updated_at'
        ]

        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]