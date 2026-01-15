# ===================================================================
# config/urls.py - CORRIGIDO
# ===================================================================
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # ✅ API v1 - Todas as rotas dentro de api/v1/
    path('api/v1/', include([
        # Autenticação
        path('auth/', include('apps.users.urls')),
        
        # Apps
        path('schools/', include('apps.schools.urls')),
        path('contacts/', include('apps.contacts.urls')),
        path('events/', include('apps.events.urls')),
        path('faqs/', include('apps.faqs.urls')),
        path('documents/', include('apps.documents.urls')),
        path('dashboard/', include('apps.dashboard.urls')),
        path('tickets/', include('apps.tickets.urls')),
        path('leads/', include('apps.leads.urls')),
        
        # ✅ CORRIGIDO: Documentação sem duplicar 'api/'
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ])),

    # DRF Auth (para browsable API em desenvolvimento)
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
