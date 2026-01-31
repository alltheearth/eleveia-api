# ===================================================================
# PASSO 3: apps/dashboard/models.py
# ===================================================================
# Cole este conteúdo SUBSTITUINDO o arquivo apps/dashboard/models.py atual

from django.db import models
from django.utils import timezone


class DashboardSnapshot(models.Model):
    """
    Snapshots diários/mensais de métricas.
    Gerado automaticamente pelo Celery.
    """

    SNAPSHOT_TYPES = [
        ('daily', 'Diário'),
        ('monthly', 'Mensal'),
    ]

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='dashboard_snapshots',
        verbose_name='Escola'
    )

    snapshot_type = models.CharField(
        max_length=20,
        choices=SNAPSHOT_TYPES,
        default='daily',
        verbose_name='Tipo'
    )

    snapshot_date = models.DateField(
        verbose_name='Data',
        db_index=True
    )

    # LEADS
    leads_total = models.IntegerField(default=0)
    leads_new = models.IntegerField(default=0)
    leads_in_contact = models.IntegerField(default=0)
    leads_qualified = models.IntegerField(default=0)
    leads_converted = models.IntegerField(default=0)
    leads_lost = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    leads_by_origin = models.JSONField(default=dict)

    # CONTATOS
    contacts_total = models.IntegerField(default=0)
    contacts_active = models.IntegerField(default=0)
    contacts_inactive = models.IntegerField(default=0)

    # TICKETS
    tickets_total = models.IntegerField(default=0)
    tickets_open = models.IntegerField(default=0)
    tickets_closed = models.IntegerField(default=0)

    # EVENTOS
    events_total = models.IntegerField(default=0)
    events_upcoming = models.IntegerField(default=0)

    # FAQs
    faqs_total = models.IntegerField(default=0)
    faqs_active = models.IntegerField(default=0)

    # METADADOS
    created_at = models.DateTimeField(auto_now_add=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'dashboard_snapshots'
        verbose_name = 'Dashboard Snapshot'
        verbose_name_plural = 'Dashboard Snapshots'
        ordering = ['-snapshot_date']
        unique_together = [['school', 'snapshot_type', 'snapshot_date']]
        indexes = [
            models.Index(fields=['school', 'snapshot_date']),
        ]

    def __str__(self):
        return f"{self.school.school_name} - {self.snapshot_date}"

    def save(self, *args, **kwargs):
        # Auto-calcular taxa de conversão
        if self.leads_total > 0:
            self.conversion_rate = (self.leads_converted / self.leads_total) * 100
        super().save(*args, **kwargs)


class DashboardCache(models.Model):
    """
    Cache de métricas em tempo real (atualizado a cada 15 min).
    """

    school = models.OneToOneField(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='dashboard_cache',
        primary_key=True
    )

    # Mesmos campos do Snapshot
    leads_total = models.IntegerField(default=0)
    leads_new = models.IntegerField(default=0)
    leads_in_contact = models.IntegerField(default=0)
    leads_qualified = models.IntegerField(default=0)
    leads_converted = models.IntegerField(default=0)
    leads_lost = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    leads_by_origin = models.JSONField(default=dict)

    contacts_total = models.IntegerField(default=0)
    contacts_active = models.IntegerField(default=0)
    contacts_inactive = models.IntegerField(default=0)

    tickets_total = models.IntegerField(default=0)
    tickets_open = models.IntegerField(default=0)
    tickets_closed = models.IntegerField(default=0)

    events_total = models.IntegerField(default=0)
    events_upcoming = models.IntegerField(default=0)

    faqs_total = models.IntegerField(default=0)
    faqs_active = models.IntegerField(default=0)

    # Controle de cache
    last_updated = models.DateTimeField(auto_now=True)
    update_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'dashboard_cache'
        verbose_name = 'Dashboard Cache'

    def __str__(self):
        return f"Cache: {self.school.school_name}"