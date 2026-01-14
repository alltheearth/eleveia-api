# ===================================================================
# apps/events/models.py - COMPLETE REFACTORED VERSION
# ===================================================================
from django.db import models
from django.contrib.auth.models import User


class CalendarEvent(models.Model):
    """School calendar events"""

    EVENT_TYPE_CHOICES = [
        ('holiday', '📌 Feriado'),
        ('exam', '📝 Prova/Avaliação'),
        ('graduation', '🎓 Formatura'),
        ('cultural', '🎉 Evento Cultural'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_events',
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='calendar_events',
        verbose_name='Escola'
    )

    date = models.DateField(verbose_name='Data')

    title = models.CharField(
        max_length=255,
        verbose_name='Título'
    )

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name='Tipo'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Evento do Calendário'
        verbose_name_plural = 'Eventos do Calendário'
        db_table = 'events_calendarevent'
        ordering = ['date']

    def __str__(self):
        return f"{self.title} - {self.date}"
