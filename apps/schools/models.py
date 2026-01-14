# ===================================================================
# apps/schools/models.py - COMPLETE REFACTORED VERSION
# ===================================================================
from django.db import models
from django.core.validators import RegexValidator


class School(models.Model):
    """Educational institution in the system"""

    # Protected fields (superuser only)
    school_name = models.CharField(
        max_length=255,
        verbose_name='Nome da Escola',
        help_text='School name (superuser only)'
    )

    tax_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='CNPJ',
        validators=[
            RegexValidator(
                regex=r'^\d{14}$',
                message='Tax ID must be exactly 14 digits (CNPJ)'
            )
        ],
        help_text='Brazilian CNPJ (superuser only)'
    )

    messaging_token = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Token de Mensagens',
        help_text='WhatsApp API token (superuser only)'
    )

    # Contact information
    phone = models.CharField(
        max_length=20,
        verbose_name='Telefone'
    )

    email = models.EmailField(
        verbose_name='Email'
    )

    website = models.URLField(
        blank=True,
        null=True,
        verbose_name='Site'
    )

    logo = models.ImageField(
        upload_to='schools/logos/',
        blank=True,
        null=True,
        verbose_name='Logo'
    )

    # Address
    postal_code = models.CharField(
        max_length=10,
        verbose_name='CEP'
    )

    street_address = models.CharField(
        max_length=255,
        verbose_name='Endereço'
    )

    city = models.CharField(
        max_length=100,
        verbose_name='Cidade'
    )

    state = models.CharField(
        max_length=2,
        verbose_name='Estado'
    )

    address_complement = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Complemento'
    )

    # Additional info
    about = models.TextField(
        blank=True,
        verbose_name='Sobre'
    )

    teaching_levels = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Níveis de Ensino',
        help_text='{"elementary": true, "high_school": false}'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Escola'
        verbose_name_plural = 'Escolas'
        ordering = ['-created_at']
        db_table = 'schools_school'
        indexes = [
            models.Index(fields=['tax_id']),
            models.Index(fields=['city', 'state']),
        ]

    def __str__(self):
        return self.school_name

    @property
    def protected_fields(self):
        """Fields only superusers can modify"""
        return ['school_name', 'tax_id', 'messaging_token']