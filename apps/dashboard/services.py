# ===================================================================
# PASSO 4: apps/dashboard/services.py (CRIAR ARQUIVO NOVO)
# ===================================================================

import logging
from datetime import timedelta
from django.db.models import Count
from django.utils import timezone
from django.core.cache import cache

from apps.schools.models import School
from .models import DashboardSnapshot, DashboardCache

logger = logging.getLogger(__name__)


class DashboardSnapshotService:
    """Gera snapshots de métricas"""

    def __init__(self, school: School):
        self.school = school

    def generate_snapshot(self, snapshot_type='daily', snapshot_date=None):
        """Gera um snapshot completo"""
        if snapshot_date is None:
            snapshot_date = timezone.now().date()

        logger.info(f"Gerando snapshot para {self.school.school_name}")

        # Calcular métricas
        metrics = self._calculate_metrics()

        # Criar ou atualizar
        snapshot, created = DashboardSnapshot.objects.update_or_create(
            school=self.school,
            snapshot_type=snapshot_type,
            snapshot_date=snapshot_date,
            defaults=metrics
        )

        logger.info(f"✅ Snapshot {'criado' if created else 'atualizado'}")
        return snapshot

    def _calculate_metrics(self):
        """Calcula todas as métricas de uma vez"""
        from apps.leads.models import Lead
        from apps.contacts.models import WhatsAppContact
        from apps.tickets.models import Ticket
        from apps.events.models import CalendarEvent
        from apps.faqs.models import FAQ

        today = timezone.now().date()

        # LEADS
        leads_qs = Lead.objects.filter(school=self.school)
        leads_total = leads_qs.count()
        leads_new = leads_qs.filter(status='new').count()
        leads_in_contact = leads_qs.filter(status='contact').count()
        leads_qualified = leads_qs.filter(status='qualified').count()
        leads_converted = leads_qs.filter(status='conversion').count()
        leads_lost = leads_qs.filter(status='lost').count()

        leads_by_origin = dict(
            leads_qs.values('origin')
            .annotate(total=Count('id'))
            .values_list('origin', 'total')
        )

        # CONTATOS
        contacts_qs = WhatsAppContact.objects.filter(school=self.school)
        contacts_total = contacts_qs.count()
        contacts_active = contacts_qs.filter(status='active').count()
        contacts_inactive = contacts_qs.filter(status='inactive').count()

        # TICKETS
        tickets_qs = Ticket.objects.filter(school=self.school)
        tickets_total = tickets_qs.count()
        tickets_open = tickets_qs.filter(status='open').count()
        tickets_closed = tickets_qs.filter(status__in=['closed', 'resolved']).count()

        # EVENTOS
        events_qs = CalendarEvent.objects.filter(school=self.school)
        events_total = events_qs.count()
        events_upcoming = events_qs.filter(end_date__gte=today).count()

        # FAQs
        faqs_qs = FAQ.objects.filter(school=self.school)
        faqs_total = faqs_qs.count()
        faqs_active = faqs_qs.filter(status='active').count()

        return {
            'leads_total': leads_total,
            'leads_new': leads_new,
            'leads_in_contact': leads_in_contact,
            'leads_qualified': leads_qualified,
            'leads_converted': leads_converted,
            'leads_lost': leads_lost,
            'leads_by_origin': leads_by_origin,
            'contacts_total': contacts_total,
            'contacts_active': contacts_active,
            'contacts_inactive': contacts_inactive,
            'tickets_total': tickets_total,
            'tickets_open': tickets_open,
            'tickets_closed': tickets_closed,
            'events_total': events_total,
            'events_upcoming': events_upcoming,
            'faqs_total': faqs_total,
            'faqs_active': faqs_active,
        }


class DashboardCacheService:
    """Gerencia cache de métricas"""

    def __init__(self, school: School):
        self.school = school

    def update_cache(self):
        """Atualiza cache no banco e Redis"""
        logger.info(f"Atualizando cache para {self.school.school_name}")

        # Calcular métricas (reutiliza lógica do snapshot)
        snapshot_service = DashboardSnapshotService(self.school)
        metrics = snapshot_service._calculate_metrics()

        # Atualizar banco
        cache_obj, created = DashboardCache.objects.update_or_create(
            school=self.school,
            defaults=metrics
        )

        if not created:
            cache_obj.update_count += 1
            cache_obj.save(update_fields=['update_count'])

        # Atualizar Redis
        cache_key = f'dashboard_realtime:{self.school.id}'
        cache.set(cache_key, metrics, 900)  # 15 minutos

        logger.info(f"✅ Cache atualizado")
        return cache_obj

    def get_cache(self):
        """Retorna cache (Redis ou banco)"""
        cache_key = f'dashboard_realtime:{self.school.id}'

        # Tentar Redis primeiro
        data = cache.get(cache_key)
        if data:
            return data

        # Fallback para banco
        try:
            cache_obj = DashboardCache.objects.get(school=self.school)
            return {
                'leads_total': cache_obj.leads_total,
                'leads_new': cache_obj.leads_new,
                'leads_in_contact': cache_obj.leads_in_contact,
                'leads_qualified': cache_obj.leads_qualified,
                'leads_converted': cache_obj.leads_converted,
                'leads_lost': cache_obj.leads_lost,
                'conversion_rate': float(cache_obj.conversion_rate),
                'leads_by_origin': cache_obj.leads_by_origin,
                'contacts_total': cache_obj.contacts_total,
                'contacts_active': cache_obj.contacts_active,
                'contacts_inactive': cache_obj.contacts_inactive,
                'tickets_total': cache_obj.tickets_total,
                'tickets_open': cache_obj.tickets_open,
                'tickets_closed': cache_obj.tickets_closed,
                'events_total': cache_obj.events_total,
                'events_upcoming': cache_obj.events_upcoming,
                'faqs_total': cache_obj.faqs_total,
                'faqs_active': cache_obj.faqs_active,
                'last_updated': cache_obj.last_updated.isoformat(),
            }
        except DashboardCache.DoesNotExist:
            return None