# apps/dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'metrics', views.DashboardMetricsViewSet, basename='dashboard-metrics')
router.register(r'interacoes', views.InteracaoN8NViewSet, basename='interacoes-n8n')

urlpatterns = [
    # Webhook do n8n
    path('webhook/n8n/', views.n8n_webhook, name='n8n-webhook'),

    # Router
    path('', include(router.urls)),
]