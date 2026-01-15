# ===================================================================
# apps/tickets/models.py - VERSÃO CORRIGIDA
# ===================================================================
from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('pending', 'Pending'),
    ('closed', 'Closed'),
    ('resolved', 'Resolved')
]

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent')
]


class Ticket(models.Model):
    """Modelo para tickets de suporte"""

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_tickets',
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    school = models.ForeignKey(
        'schools.School',  # ✅ CORRIGIDO: era 'schools.Escola'
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='Escola',
        help_text='Escola vinculada ao ticket'
    )

    title = models.CharField(
        max_length=255,
        verbose_name='Título'
    )

    description = models.TextField(
        verbose_name='Descrição'
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Prioridade'
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='open',
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
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        db_table = 'tickets_ticket'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'status']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"