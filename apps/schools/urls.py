"""
URLs do app de escolas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.EscolaViewSet, basename='escola')

urlpatterns = [
    path('', include(router.urls)),
]