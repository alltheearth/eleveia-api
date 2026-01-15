# ===================================================================
# apps/events/urls.py - CORRIGIDO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CORRETO: Usa CalendarEventViewSet
router.register(r'', views.CalendarEventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
]