"""
✅ CORRETO - config/urls.py
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # ✅ API v1 - TODAS as rotas devem estar dentro de api/v1/
    path('api/v1/', include([
        # Autenticação
        path('auth/', include('apps.users.urls')),  # ✅ /api/v1/auth/login/

        # Escolas
        path('schools/', include('apps.schools.urls')),  # ✅ /api/v1/schools/

        # Contatos
        path('contacts/', include('apps.contacts.urls')),  # ✅ /api/v1/contacts/

        # Eventos
        path('events/', include('apps.events.urls')),  # ✅ /api/v1/events/

        # FAQs
        path('faqs/', include('apps.faqs.urls')),  # ✅ /api/v1/faqs/

        # Documentos
        path('documents/', include('apps.documents.urls')),  # ✅ /api/v1/documents/

        # Dashboard
        path('dashboard/', include('apps.dashboard.urls')),  # ✅ /api/v1/dashboard/

        # Tickets
        path('tickets/', include('apps.tickets.urls')),  # ✅ /api/v1/tickets/

        # Leads
        path('leads/', include('apps.leads.urls')),  # ✅ /api/v1/leads/
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