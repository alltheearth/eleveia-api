from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class WhatsAppContact(models.Model):
    """Contact from WhatsApp interactions"""

    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
    ]

    SOURCE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('website', 'Site'),
        ('phone_call', 'Telefone'),
        ('in_person', 'Presencial'),
        ('email', 'Email'),
        ('referral', 'Indicação'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_contacts',
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='whatsapp_contacts',
        verbose_name='Escola'
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nome Completo'
    )

    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )

    phone = models.CharField(
        max_length=20,
        verbose_name='Telefone'
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Nascimento'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='whatsapp',
        verbose_name='Origem'
    )

    last_interaction_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Interação'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )

    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Tags'
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
        verbose_name = 'Contato WhatsApp'
        verbose_name_plural = 'Contatos WhatsApp'
        db_table = 'contacts_whatsappcontact'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'status']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name='whatsappcontact_must_have_contact_info'
            )
        ]

    def __str__(self):
        name = self.full_name or self.phone
        return f"{name} - {self.get_status_display()}"