
# ===================================================================
# apps/schools/urls.py - CORRIGIDO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CORRETO: Usa SchoolViewSet
router.register(r'', views.SchoolViewSet, basename='school')

urlpatterns = [
    path('', include(router.urls)),
]