# ===================================================================
# apps/faqs/serializers.py - ENGLISH VERSION
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
        read_only_fields = ['id', 'created_at', 'updated_at', 'school_name']

    def validate_question(self, value):
        """Validate question"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Question must be at least 10 characters long"
            )
        return value.strip()

    def validate_answer(self, value):
        """Validate answer"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Answer must be at least 3 characters long"
            )
        return value.strip()