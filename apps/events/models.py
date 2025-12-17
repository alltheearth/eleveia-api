from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class CalendarioEvento(models.Model):
    """Modelo para armazenar eventos do calendário escolar"""
    TIPO_CHOICES = [
        ('feriado', '📌 Feriado'),
        ('prova', '📝 Prova/Avaliação'),
        ('formatura', '🎓 Formatura'),
        ('evento_cultural', '🎉 Evento Cultural'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='eventos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='eventos'
    )

    data = models.DateField()
    evento = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['data']
        verbose_name = 'Evento do Calendário'
        verbose_name_plural = 'Eventos do Calendário'

    def __str__(self):
        return f"{self.evento} - {self.data}"
