# apps/events/serializers.py - UPDATED
from rest_framework import serializers
from .models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    """Calendar event serializer with validation"""

    school_name = serializers.CharField(
        source='school.school_name',
        read_only=True
    )
    event_type_display = serializers.CharField(
        source='get_event_type_display',
        read_only=True
    )
    duration_days = serializers.IntegerField(read_only=True)
    is_single_day = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = CalendarEvent
        fields = [
            'id',
            'school',
            'school_name',
            'start_date',
            'end_date',
            'title',
            'description',
            'event_type',
            'event_type_display',
            'duration_days',
            'is_single_day',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'school_name',
            'event_type_display',
            'duration_days',
            'is_single_day',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # If updating, get existing values
        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date

        if start_date and end_date:
            if end_date < start_date:
                raise serializers.ValidationError({
                    'end_date': 'End date cannot be before start date.'
                })

        return data