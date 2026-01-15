# ===================================================================
# apps/leads/urls.py - CORRIGIDO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CORRETO: Usa LeadViewSet (não TicketViewSet)
router.register(r'', views.LeadViewSet, basename='lead')

urlpatterns = [
    path('', include(router.urls)),
]