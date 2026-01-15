# ===================================================================
# apps/dashboard/views.py - IMPLEMENTAÇÃO COMPLETA
# ===================================================================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from core.permissions import IsSchoolStaff
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


@api_view(['GET'])
@permission_classes([IsSchoolStaff])
def metrics(request):
    """
    Retorna métricas gerais do dashboard.

    Superuser pode filtrar por escola usando ?school_id=X
    Staff vê apenas da sua escola
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

    # Imports dinâmicos (para evitar erros se apps não existirem)
    try:
        from apps.contacts.models import WhatsAppContact
        from apps.faqs.models import FAQ
        from apps.events.models import CalendarEvent
        from apps.tickets.models import Ticket
        from apps.leads.models import Lead
    except ImportError as e:
        return Response({
            'error': 'Some apps are not properly configured',
            'details': str(e)
        }, status=500)

    # Datas de referência
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)

    # Calcular métricas
    metrics = {
        'contacts': {
            'total': WhatsAppContact.objects.filter(school_filter).count(),
            'active': WhatsAppContact.objects.filter(
                school_filter,
                status='active'
            ).count(),
            'inactive': WhatsAppContact.objects.filter(
                school_filter,
                status='inactive'
            ).count(),
            'recent_interactions': WhatsAppContact.objects.filter(
                school_filter,
                last_interaction_at__gte=week_ago
            ).count(),
        },
        'faqs': {
            'total': FAQ.objects.filter(school_filter).count(),
            'active': FAQ.objects.filter(
                school_filter,
                status='active'
            ).count(),
        },
        'events': {
            'total': CalendarEvent.objects.filter(school_filter).count(),
            'upcoming': CalendarEvent.objects.filter(
                school_filter,
                date__gte=today
            ).count(),
        },
        'tickets': {
            'total': Ticket.objects.filter(school_filter).count(),
            'open': Ticket.objects.filter(
                school_filter,
                status='open'
            ).count(),
            'in_progress': Ticket.objects.filter(
                school_filter,
                status='in_progress'
            ).count(),
            'closed': Ticket.objects.filter(
                school_filter,
                status__in=['closed', 'resolved']
            ).count(),
        },
        'leads': {
            'total': Lead.objects.filter(school_filter).count(),
            'new': Lead.objects.filter(
                school_filter,
                status='new'
            ).count(),
            'in_contact': Lead.objects.filter(
                school_filter,
                status='contact'
            ).count(),
            'qualified': Lead.objects.filter(
                school_filter,
                status='qualified'
            ).count(),
            'converted': Lead.objects.filter(
                school_filter,
                status='conversion'
            ).count(),
            'lost': Lead.objects.filter(
                school_filter,
                status='lost'
            ).count(),
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