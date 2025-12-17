from django.db import models
from django.contrib.auth.models import User
from apps.schools.models import Escola

class Dashboard(models.Model):
    """Modelo para armazenar dados do dashboard"""
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards',
        null=True,
        blank=True
    )
    escola = models.OneToOneField(
        Escola,
        on_delete=models.CASCADE,
        related_name='dashboard'
    )

    status_agente = models.CharField(max_length=20, default='ativo')
    interacoes_hoje = models.IntegerField(default=0)
    documentos_upload = models.IntegerField(default=0)
    faqs_criadas = models.IntegerField(default=0)

    leads_capturados = models.IntegerField(default=0)
    taxa_resolucao = models.IntegerField(default=0)
    novos_hoje = models.IntegerField(default=0)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

    def __str__(self):
        return f"Dashboard - {self.escola.nome_escola}"
