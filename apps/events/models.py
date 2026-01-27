# apps/events/models.py - UPDATED WITH DATE RANGE
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CalendarEvent(models.Model):
    """School calendar events with date range support"""

    EVENT_TYPE_CHOICES = [
        ('holiday', '📌 Holiday'),
        ('exam', '📝 Exam/Assessment'),
        ('graduation', '🎓 Graduation'),
        ('cultural', '🎉 Cultural Event'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_events',
        null=True,
        blank=True,
        verbose_name='Created by'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='calendar_events',
        verbose_name='School'
    )

    # ✅ NEW: Date range instead of single date
    start_date = models.DateField(verbose_name='Start Date')
    end_date = models.DateField(verbose_name='End Date')

    title = models.CharField(
        max_length=255,
        verbose_name='Title'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name='Type'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )

    class Meta:
        verbose_name = 'Calendar Event'
        verbose_name_plural = 'Calendar Events'
        db_table = 'events_calendarevent'
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['school', 'start_date']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"

    def clean(self):
        """Validate that end_date >= start_date"""
        super().clean()
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'End date cannot be before start date.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def duration_days(self):
        """Calculate event duration in days"""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_single_day(self):
        """Check if event is a single day"""
        return self.start_date == self.end_date