# ===================================================================
# apps/faqs/models.py - COMPLETE REFACTORED VERSION
# ===================================================================
from django.db import models
from django.contrib.auth.models import User


class FAQ(models.Model):
    """Frequently Asked Questions"""

    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('inactive', 'Inativa'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_faqs',
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='Escola'
    )

    question = models.CharField(
        max_length=500,
        verbose_name='Pergunta'
    )

    answer = models.TextField(
        blank=True,
        verbose_name='Resposta'
    )

    category = models.CharField(
        max_length=100,
        verbose_name='Categoria'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
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
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        db_table = 'faqs_faq'
        ordering = ['-created_at']

    def __str__(self):
        return self.question
