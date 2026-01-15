# ===================================================================
# apps/leads/models.py - VERSÃO CORRIGIDA
# ===================================================================
from django.db import models
from django.contrib.auth.models import User


class Lead(models.Model):
    """Modelo para leads capturados pelo agente IA"""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('contact', 'In Contact'),
        ('qualified', 'Qualified'),
        ('conversion', 'Conversion'),
        ('lost', 'Lost'),
    ]

    ORIGIN_CHOICES = [
        ('site', 'Site'),
        ('whatsapp', 'WhatsApp'),
        ('recommendation', 'Recommendation'),
        ('call', 'Call'),
        ('email', 'Email'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_leads',
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    school = models.ForeignKey(
        'schools.School',  # ✅ CORRIGIDO: era 'schools.Escola'
        on_delete=models.CASCADE,
        related_name='leads',
        verbose_name='Escola'
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )

    email = models.EmailField(
        verbose_name='Email'
    )

    telephone = models.CharField(
        max_length=20,
        verbose_name='Telefone'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Status'
    )

    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
        default='whatsapp',
        verbose_name='Origem'
    )

    observations = models.TextField(
        blank=True,
        verbose_name='Observações'
    )

    interests = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Interesses'
    )

    contacted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Contatado em'
    )

    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Convertido em'
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
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        db_table = 'leads_lead'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"