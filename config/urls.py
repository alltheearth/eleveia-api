"""
Configuração de URLs principais
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Router principal
router = DefaultRouter()

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include([
        # Autenticação
        path('auth/', include('apps.users.urls')),

        # Escolas
        path('schools/', include('apps.schools.urls')),

        # CRM
        path('contacts/', include('apps.contacts.urls')),

        # Eventos
        path('events/', include('apps.events.urls')),

        # FAQs
        path('faqs/', include('apps.faqs.urls')),

        # Documentos
        path('documents/', include('apps.documents.urls')),

        # Dashboard
        path('dashboard/', include('apps.dashboard.urls')),
    ])),

    # DRF Auth (para browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# Servir arquivos estáticos e media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customizar admin
admin.site.site_header = "EleveAI Admin"
admin.site.site_title = "EleveAI"
admin.site.index_title = "Gestão de Escolas"