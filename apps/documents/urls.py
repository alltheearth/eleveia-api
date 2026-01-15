
# ===================================================================
# apps/documents/urls.py - CORRIGIDO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CORRETO: Usa DocumentViewSet
router.register(r'', views.DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]