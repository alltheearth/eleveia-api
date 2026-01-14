# ===================================================================
# apps/documents/models.py - COMPLETE REFACTORED VERSION
# ===================================================================
from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    """School documents"""

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('processed', 'Processado'),
        ('error', 'Erro'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_documents',
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Escola'
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )

    file = models.FileField(
        upload_to='documents/',
        verbose_name='Arquivo'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
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
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        db_table = 'documents_document'
        ordering = ['-created_at']

    def __str__(self):
        return self.name