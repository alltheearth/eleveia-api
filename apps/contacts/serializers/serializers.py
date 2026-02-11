# ===================================================================
# apps/contacts/serializers.py
# ===================================================================
from rest_framework import serializers
# from apps.contacts.models import WhatsAppContact


class WhatsAppContactSerializer(serializers.ModelSerializer):
    """WhatsApp contact serializer"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:

        fields = [
            'id',
            'school',
            'school_name',
            'full_name',
            'email',
            'phone',
            'date_of_birth',
            'status',
            'status_display',
            'source',
            'source_display',
            'last_interaction_at',
            'notes',
            'tags',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'school_name',
            'status_display',
            'source_display',
            'created_at',
            'updated_at',
        ]
