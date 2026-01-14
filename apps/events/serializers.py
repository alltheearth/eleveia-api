# ===================================================================
# apps/events/serializers.py
# ===================================================================
from rest_framework import serializers
from .models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    """Calendar event serializer"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = CalendarEvent
        fields = [
            'id',
            'school',
            'school_name',
            'date',
            'title',
            'event_type',
            'event_type_display',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'school_name', 'event_type_display', 'created_at', 'updated_at']