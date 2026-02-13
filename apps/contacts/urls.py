# apps/contacts/urls.py

"""
✨ URLs ATUALIZADAS - Rota Unificada

ANTES (rotas antigas - REMOVIDAS):
- /students/guardians/  → StudentGuardianView
- /students/invoices/   → StudentInvoiceView
- /guardians/           → StudentsGuardiansView

DEPOIS (rota única - NOVA):
- /guardians/           → GuardianUnifiedView

Features da nova rota:
- ✅ Responsáveis + Filhos + Boletos integrados
- ✅ Filtros avançados (search, email, CPF, telefone, situação)
- ✅ Ordenação alfabética automática
- ✅ Cache 2 horas
- ✅ Paginação 20/página
- ✅ Documentação OpenAPI completa
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.contact_views import ContatoViewSet
from .views.guardian_unified_view import GuardianUnifiedView

# ===================================================================
# ROUTER PARA VIEWSETS
# ===================================================================
router = DefaultRouter()

# ✅ CRUD de Contatos (antes não estava registrado!)
router.register(r'contatos', ContatoViewSet, basename='contato')

# ===================================================================
# URL PATTERNS
# ===================================================================
urlpatterns = [
    # ✨ NOVA ROTA UNIFICADA - Responsáveis + Filhos + Boletos
    path(
        'guardians/',
        GuardianUnifiedView.as_view(),
        name='guardians-unified'
    ),

    # ✅ CRUD de Contatos (ViewSet)
    path('', include(router.urls)),
]

# ===================================================================
# ROTAS DISPONÍVEIS APÓS ATUALIZAÇÃO:
# ===================================================================
#
# ViewSet de Contatos:
# - GET    /api/v1/contacts/contatos/              → Lista contatos
# - GET    /api/v1/contacts/contatos/{id}/         → Detalhes de contato
# - POST   /api/v1/contacts/contatos/              → Cria contato
# - PUT    /api/v1/contacts/contatos/{id}/         → Atualiza contato (full)
# - PATCH  /api/v1/contacts/contatos/{id}/         → Atualiza contato (partial)
# - DELETE /api/v1/contacts/contatos/{id}/         → Remove contato
# - GET    /api/v1/contacts/contatos/ativos/       → Ação customizada (apenas ativos)
#
# Responsáveis Unificados:
# - GET    /api/v1/contacts/guardians/             → Lista responsáveis (com filtros)
#
# Exemplos de uso:
# - GET /api/v1/contacts/guardians/?search=Maria
# - GET /api/v1/contacts/guardians/?email=ana@example.com
# - GET /api/v1/contacts/guardians/?cpf=12345678900
# - GET /api/v1/contacts/guardians/?telefone=11987654321
# - GET /api/v1/contacts/guardians/?tem_boleto_aberto=true
# - GET /api/v1/contacts/guardians/?tem_doc_faltando=true
# - GET /api/v1/contacts/guardians/?search=Silva&tem_boleto_aberto=true
# - GET /api/v1/contacts/guardians/?page=2&page_size=50
#
# ===================================================================