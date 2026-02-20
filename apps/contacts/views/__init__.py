# apps/contacts/views/__init__.py

from .contact_views import ContatoViewSet
from .guardian_viewset import GuardianViewSet
from .dashboard_views import SchoolDashboardView

__all__ = [
    'ContatoViewSet',
    'GuardianViewSet',
    'SchoolDashboardView',
]