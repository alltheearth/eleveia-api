# apps/contacts/urls.py

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URLs do módulo Contacts — VERSÃO DEFINITIVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ROTAS GERADAS:

Guardians (Responsáveis) — via Router:
  GET    /api/v1/contacts/guardians/                  → list
  GET    /api/v1/contacts/guardians/{id}/             → retrieve
  GET    /api/v1/contacts/guardians/{id}/invoices/    → invoices
  GET    /api/v1/contacts/guardians/stats/            → stats
  POST   /api/v1/contacts/guardians/refresh/          → refresh

Contatos (CRUD local) — via Router:
  GET    /api/v1/contacts/contatos/                   → list
  POST   /api/v1/contacts/contatos/                   → create
  GET    /api/v1/contacts/contatos/{id}/              → retrieve
  PUT    /api/v1/contacts/contatos/{id}/              → update
  PATCH  /api/v1/contacts/contatos/{id}/              → partial_update
  DELETE /api/v1/contacts/contatos/{id}/              → destroy
  GET    /api/v1/contacts/contatos/ativos/            → ativos

Dashboard:
  GET    /api/v1/contacts/dashboard/                  → dashboard stats
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.contact_views import ContatoViewSet
from .views.guardian_viewset import GuardianViewSet
from .views.dashboard_views import SchoolDashboardView

# ===================================================================
# ROUTER
# ===================================================================

router = DefaultRouter()

# Guardians — o ViewSet cuida de list, retrieve, invoices, stats, refresh
router.register(r'guardians', GuardianViewSet, basename='guardian')

# Contatos — CRUD local (não depende do SIGA)
router.register(r'contatos', ContatoViewSet, basename='contato')

# ===================================================================
# URL PATTERNS
# ===================================================================

urlpatterns = [
    # Dashboard (view isolada, não precisa de router)
    path('dashboard/', SchoolDashboardView.as_view(), name='school-dashboard'),

    # Todas as rotas do router
    path('', include(router.urls)),
]