# ===================================================================
# PASSO 6: apps/dashboard/urls.py
# ===================================================================
# SUBSTITUIR o arquivo apps/dashboard/urls.py atual

from django.urls import path
from . import views

urlpatterns = [
    # ⚡ CACHE - Rápido (~50ms) - USE ESTE NO DASHBOARD
    path('realtime/', views.realtime_metrics, name='dashboard-realtime'),

    # 🔥 SEM CACHE - Preciso (~300ms) - Use quando precisar dados exatos
    path('metrics/', views.metrics, name='dashboard-metrics'),
]