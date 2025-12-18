"""
URLs do app de tickets
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TicketViewSet, basename='leads')

urlpatterns = [
    path('', include(router.urls)),
]