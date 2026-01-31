# ===================================================================
# PASSO 9: apps/dashboard/tasks.py (CRIAR ARQUIVO NOVO)
# ===================================================================

from celery import shared_task
import logging

from apps.schools.models import School
from .services import DashboardCacheService, DashboardSnapshotService

logger = logging.getLogger(__name__)


@shared_task(name='apps.dashboard.tasks.update_all_caches')
def update_all_caches():
    """
    Atualiza cache de TODAS as escolas.
    Executado automaticamente a cada 15 minutos.
    """
    logger.info("🔄 Atualizando cache de todas as escolas...")

    schools = School.objects.all()

    success = 0
    failed = 0

    for school in schools:
        try:
            service = DashboardCacheService(school)
            service.update_cache()
            success += 1
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar cache de {school.school_name}: {e}")
            failed += 1

    logger.info(f"✅ Cache atualizado: {success} sucessos, {failed} falhas")

    return {
        'success': success,
        'failed': failed,
        'total': schools.count()
    }


@shared_task(name='apps.dashboard.tasks.generate_daily_snapshots')
def generate_daily_snapshots():
    """
    Gera snapshots diários para TODAS as escolas.
    Executado automaticamente todo dia às 00:05.
    """
    logger.info("📸 Gerando snapshots diários...")

    schools = School.objects.all()

    success = 0
    failed = 0

    for school in schools:
        try:
            service = DashboardSnapshotService(school)
            service.generate_snapshot(snapshot_type='daily')
            success += 1
        except Exception as e:
            logger.error(f"❌ Erro ao gerar snapshot de {school.school_name}: {e}")
            failed += 1

    logger.info(f"✅ Snapshots gerados: {success} sucessos, {failed} falhas")

    return {
        'success': success,
        'failed': failed,
        'total': schools.count()
    }


@shared_task(name='apps.dashboard.tasks.update_cache_for_school')
def update_cache_for_school(school_id: int):
    """
    Atualiza cache de UMA escola específica.
    Útil para chamar manualmente.
    """
    try:
        school = School.objects.get(id=school_id)
        service = DashboardCacheService(school)
        service.update_cache()
        logger.info(f"✅ Cache atualizado para {school.school_name}")
        return {'success': True, 'school_id': school_id}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return {'success': False, 'error': str(e)}