# ===================================================================
# apps/faqs/serializers.py
# ===================================================================
from rest_framework import serializers
from .models import FAQ


class FAQSerializer(serializers.ModelSerializer):
    """FAQ serializer"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = FAQ
        fields = [
            'id',
            'school',
            'school_name',
            'question',
            'answer',
            'category',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'school_name', 'created_at', 'updated_at']