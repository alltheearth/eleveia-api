# apps/contacts/tasks.py
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


@shared_task(bind=True, max_retries=3)
def fetch_all_invoices_task(self, school_id, token):
    """
    Task Celery para buscar boletos em background
    """
    cache_key = f"all_invoices_school_{school_id}"
    processing_key = f"invoice_processing_{school_id}"

    try:
        # Marcar como processando
        cache.set(processing_key, True, timeout=600)

        # Buscar dados
        invoices_data = _fetch_invoices_parallel(token)

        # Salvar no cache (1 hora)
        cache.set(cache_key, invoices_data, timeout=3600)

        return {"status": "success", "total_invoices": invoices_data['summary']['total_invoices']}

    except Exception as e:
        return {"status": "error", "error": str(e)}

    finally:
        cache.delete(processing_key)


def _fetch_invoices_parallel(token):
    """Implementação igual ao método da view"""
    # ... (copiar código de _fetch_all_invoices_parallel)
    pass