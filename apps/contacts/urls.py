# ===================================================================
# apps/contacts/urls.py - CORRIGIDO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CORRETO: Usa WhatsAppContactViewSet
router.register(r'', views.WhatsAppContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
