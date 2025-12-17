from django.db import models
from django.contrib.auth.models import User
from apps.schools.models import Escola

class Documento(models.Model):
    """Modelo para armazenar documentos da escola"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('processado', 'Processado'),
        ('erro', 'Erro'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documentos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='documentos'
    )

    nome = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='documentos/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return self.nome