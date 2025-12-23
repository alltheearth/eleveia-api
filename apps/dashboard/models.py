# apps/dashboard/models.py
from django.db import models
from apps.schools.models import Escola


class DashboardMetrics(models.Model):
    """Métricas do dashboard vindas do n8n"""

    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='dashboard_metrics'
    )

    # Métricas principais
    total_interacoes = models.IntegerField(default=0)
    interacoes_hoje = models.IntegerField(default=0)
    leads_capturados = models.IntegerField(default=0)
    tickets_abertos = models.IntegerField(default=0)

    # Métricas de performance
    tempo_medio_resposta = models.CharField(max_length=20, default='0min')
    taxa_satisfacao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxa_conversao = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Status do agente
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('ocupado', 'Ocupado'),
    ]
    status_agente = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='online'
    )

    # Metadados do n8n
    n8n_workflow_id = models.CharField(max_length=100, blank=True)
    n8n_execution_id = models.CharField(max_length=100, blank=True)

    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard Metrics'
        verbose_name_plural = 'Dashboard Metrics'
        ordering = ['-atualizado_em']
        indexes = [
            models.Index(fields=['escola', '-atualizado_em']),
        ]

    def __str__(self):
        return f"Metrics - {self.escola.nome_escola} - {self.atualizado_em}"


class InteracaoN8N(models.Model):
    """Log de interações vindas do n8n"""

    TIPO_CHOICES = [
        ('mensagem', 'Mensagem'),
        ('lead', 'Lead Capturado'),
        ('ticket', 'Ticket Criado'),
        ('contato', 'Contato Registrado'),
    ]

    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='interacoes_n8n'
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)

    # Dados estruturados da interação
    dados = models.JSONField(default=dict)

    # Metadados do n8n
    n8n_workflow_id = models.CharField(max_length=100, blank=True)
    n8n_execution_id = models.CharField(max_length=100, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Interação N8N'
        verbose_name_plural = 'Interações N8N'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['escola', '-criado_em']),
            models.Index(fields=['tipo', '-criado_em']),
        ]

    def __str__(self):
        return f"{self.tipo} - {self.titulo}"