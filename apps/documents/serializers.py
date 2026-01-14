# ===================================================================
# apps/documents/serializers.py
# ===================================================================
from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id',
            'school',
            'school_name',
            'name',
            'file',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'school_name', 'created_at', 'updated_at']