from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from eleveai.views import (
    EscolaViewSet, ContatoViewSet, CalendarioEventoViewSet,
    FAQViewSet, DocumentoViewSet, DashboardViewSet
)

router = DefaultRouter()
router.register(r'escolas', EscolaViewSet, basename='escola')
router.register(r'contatos', ContatoViewSet, basename='contato')
router.register(r'eventos', CalendarioEventoViewSet, basename='evento')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'documentos', DocumentoViewSet, basename='documento')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]