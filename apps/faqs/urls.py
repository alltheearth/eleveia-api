
# ===================================================================
# apps/faqs/urls.py - JÁ ESTÁ CORRETO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.FAQViewSet, basename='faq')

urlpatterns = [
    path('', include(router.urls)),
]