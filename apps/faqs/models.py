from django.db import models
from django.contrib.auth.models import User
from apps.schools.models import Escola


class FAQ(models.Model):
    """Modelo para armazenar perguntas frequentes"""
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('inativa', 'Inativa'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='faqs',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='faqs'
    )

    pergunta = models.CharField(max_length=500)
    resposta = models.TextField(blank=True)
    categoria = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ativa')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['-criado_em']

    def __str__(self):
        return self.pergunta
