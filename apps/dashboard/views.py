# ===================================================================
# PASSO 5: apps/dashboard/views.py
# ===================================================================
# SUBSTITUIR o arquivo apps/dashboard/views.py atual por este

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count

from core.permissions import IsSchoolStaff
from .services import DashboardCacheService


# ===================================================================
# ENDPOINT PRINCIPAL - MÉTRICAS EM TEMPO REAL (COM CACHE)
# ===================================================================

@api_view(['GET'])
@permission_classes([IsSchoolStaff])
def realtime_metrics(request):
    """
    📊 GET /api/v1/dashboard/realtime/

    Retorna métricas em cache (atualizado a cada 15 min via Celery).

    Query Params:
        force_update (bool): Força recalculo (ignore cache)
    """
    user = request.user

    # Determinar escola
    if user.is_superuser or user.is_staff:
        school_id = request.query_params.get('school_id')
        if not school_id:
            return Response(
                {'error': 'Superuser must specify school_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            from apps.schools.models import School
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            return Response(
                {'error': 'School not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        if not hasattr(user, 'profile') or not user.profile.school:
            return Response(
                {'error': 'User has no school'},
                status=status.HTTP_403_FORBIDDEN
            )
        school = user.profile.school

    # Verificar se deve forçar atualização
    force_update = request.query_params.get('force_update', 'false').lower() == 'true'

    # Pegar cache
    cache_service = DashboardCacheService(school)

    if force_update:
        cache_service.update_cache()

    metrics = cache_service.get_cache()

    if not metrics:
        # Cache não existe, criar
        cache_service.update_cache()
        metrics = cache_service.get_cache()

    # Calcular idade do cache
    last_updated = metrics.get('last_updated')
    if last_updated:
        from datetime import datetime
        if isinstance(last_updated, str):
            last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        else:
            last_updated_dt = last_updated
        cache_age = (timezone.now() - last_updated_dt).total_seconds()
    else:
        cache_age = 0

    return Response({
        'metrics': metrics,
        'last_updated': last_updated,
        'cache_age_seconds': int(cache_age),
        'school': {
            'id': school.id,
            'name': school.school_name
        }
    })


# ===================================================================
# ENDPOINT ALTERNATIVO - MÉTRICAS SEM CACHE (SEMPRE ATUAL)
# ===================================================================

@api_view(['GET'])
@permission_classes([IsSchoolStaff])
def metrics(request):
    """
    📊 GET /api/v1/dashboard/metrics/

    Retorna métricas calculadas em tempo real (SEM cache).
    Mais lento, mas sempre 100% atual.
    """
    user = request.user

    # Determinar filtro de escola
    if user.is_superuser or user.is_staff:
        school_id = request.query_params.get('school_id')
        school_filter = Q(school_id=school_id) if school_id else Q()
    else:
        if not hasattr(user, 'profile') or not user.profile.school:
            return Response({'error': 'User has no school'}, status=403)
        school_filter = Q(school=user.profile.school)

    # Imports
    try:
        from apps.contacts.models import WhatsAppContact
        from apps.faqs.models import FAQ
        from apps.events.models import CalendarEvent
        from apps.tickets.models import Ticket
        from apps.leads.models import Lead
    except ImportError as e:
        return Response({
            'error': 'Some apps are not configured',
            'details': str(e)
        }, status=500)

    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)

    # Calcular métricas
    metrics = {
        'contacts': {
            'total': WhatsAppContact.objects.filter(school_filter).count(),
            'active': WhatsAppContact.objects.filter(
                school_filter, status='active'
            ).count(),
            'inactive': WhatsAppContact.objects.filter(
                school_filter, status='inactive'
            ).count(),
            'recent_interactions': WhatsAppContact.objects.filter(
                school_filter, last_interaction_at__gte=week_ago
            ).count(),
        },
        'faqs': {
            'total': FAQ.objects.filter(school_filter).count(),
            'active': FAQ.objects.filter(school_filter, status='active').count(),
        },
        'events': {
            'total': CalendarEvent.objects.filter(school_filter).count(),
            'upcoming': CalendarEvent.objects.filter(
                school_filter, end_date__gte=today
            ).count(),
        },
        'tickets': {
            'total': Ticket.objects.filter(school_filter).count(),
            'open': Ticket.objects.filter(school_filter, status='open').count(),
            'in_progress': Ticket.objects.filter(
                school_filter, status='in_progress'
            ).count(),
            'closed': Ticket.objects.filter(
                school_filter, status__in=['closed', 'resolved']
            ).count(),
        },
        'leads': {
            'total': Lead.objects.filter(school_filter).count(),
            'new': Lead.objects.filter(school_filter, status='new').count(),
            'in_contact': Lead.objects.filter(school_filter, status='contact').count(),
            'qualified': Lead.objects.filter(school_filter, status='qualified').count(),
            'converted': Lead.objects.filter(school_filter, status='conversion').count(),
            'lost': Lead.objects.filter(school_filter, status='lost').count(),
        },
    }

    # Leads por origem
    leads_by_origin = dict(
        Lead.objects.filter(school_filter)
        .values('origin')
        .annotate(total=Count('id'))
        .values_list('origin', 'total')
    )
    metrics['leads']['by_origin'] = leads_by_origin

    # Tickets por prioridade
    tickets_by_priority = dict(
        Ticket.objects.filter(school_filter)
        .values('priority')
        .annotate(total=Count('id'))
        .values_list('priority', 'total')
    )
    metrics['tickets']['by_priority'] = tickets_by_priority

    return Response(metrics)