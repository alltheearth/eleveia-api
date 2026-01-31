# ===================================================================
# PASSO 8: config/celery.py (CRIAR ARQUIVO NOVO)
# ===================================================================

import os
from celery import Celery
from celery.schedules import crontab

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('eleveai')

# Carregar configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir tasks automaticamente em todos os apps
app.autodiscover_tasks()

# ===================================================================
# SCHEDULE - Tarefas Automáticas
# ===================================================================

app.conf.beat_schedule = {
    # Atualizar cache a cada 15 minutos
    'update-dashboard-cache': {
        'task': 'apps.dashboard.tasks.update_all_caches',
        'schedule': crontab(minute='*/15'),  # A cada 15 min
    },

    # Gerar snapshot diário todo dia às 00:05
    'daily-dashboard-snapshot': {
        'task': 'apps.dashboard.tasks.generate_daily_snapshots',
        'schedule': crontab(hour=0, minute=5),  # 00:05 todo dia
    },
}


@app.task(bind=True)
def debug_task(self):
    """Task de debug"""
    print(f'Request: {self.request!r}')