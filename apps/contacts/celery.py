# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-invoice-stats-every-hour': {
        'task': 'apps.contacts.tasks.sync_all_schools_invoice_stats',
        'schedule': crontab(minute=0),  # A cada hora
    },
}