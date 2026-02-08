# tasks.py (criar novo arquivo em apps/contacts/)
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import requests


@shared_task(bind=True, max_retries=3)
def fetch_invoice_statistics(self, school_id, token, student_ids):
    """
    Task Celery para processar estatísticas de boletos em background
    """
    cache_key = f"invoice_stats_school_{school_id}"
    processing_key = f"invoice_stats_processing_{school_id}"

    try:
        # Marca como processando
        cache.set(processing_key, True, timeout=600)

        total_invoices = 0
        open_invoices = 0
        paid_invoices = 0

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        for student_id in student_ids:
            try:
                url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
                params = {'id_aluno': student_id}

                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    invoices = data.get('resultados', [])

                    for invoice in invoices:
                        total_invoices += 1
                        situacao = invoice.get('situacao_titulo', '')

                        if 'LIQ' in situacao:
                            paid_invoices += 1
                        elif 'ABE' in situacao:
                            open_invoices += 1

            except requests.exceptions.RequestException:
                continue

        # Salva resultado no cache
        now = timezone.now()
        stats = {
            'total_invoices': total_invoices,
            'open_invoices': open_invoices,
            'paid_invoices': paid_invoices,
            'completion_rate': round((paid_invoices / total_invoices * 100), 2) if total_invoices > 0 else 0,
            'last_updated': now.isoformat(),
            'next_update': (now + timedelta(hours=1)).isoformat()
        }

        cache.set(cache_key, stats, timeout=3600)

    finally:
        cache.delete(processing_key)

    return stats


# views_new.py (versão com Celery)
from .tasks import fetch_invoice_statistics


class StudentGuardianView(APIView):
    # ...

    def _get_cached_invoice_stats(self, school_id, students, token):
        cache_key = f"invoice_stats_school_{school_id}"

        # Tenta buscar do cache
        cached_stats = cache.get(cache_key)

        if cached_stats:
            return {**cached_stats, 'cached': True}

        # Verifica se já está processando
        processing_key = f"invoice_stats_processing_{school_id}"
        is_processing = cache.get(processing_key)

        if not is_processing:
            # 🚀 Dispara task Celery
            student_ids = [s.get('id') for s in students if s.get('id')]
            fetch_invoice_statistics.delay(school_id, token, student_ids)

        return {
            'total_invoices': 0,
            'open_invoices': 0,
            'paid_invoices': 0,
            'completion_rate': 0,
            'cached': False,
            'processing': True,
            'message': 'Estatísticas sendo processadas. Atualize em alguns minutos.'
        }