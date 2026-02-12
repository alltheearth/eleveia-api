# apps/contacts/urls.py
"""
URLs do módulo Contacts - REFATORADO

Estrutura:
- Endpoints NOVOS (✅): ViewSet com DRF Router
- Endpoints ANTIGOS (⚠️): Mantidos temporariamente para compatibilidade

Migração:
1. Frontend migra para /guardians/ (ViewSet)
2. Após 100% migrado, remover endpoints -old
3. Deletar views antigas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# ✅ NOVA ARQUITETURA
from .views.guardian_viewset import GuardianViewSet
from .views.student_invoice_views import StudentInvoiceView

# ⚠️ DEPRECATED - Será removido após migração do frontend
from .views.guardian_views import StudentsGuardiansView
from .views.student_guardian_views import StudentGuardianView

# ===================================================================
# DRF ROUTER (NOVA ARQUITETURA)
# ===================================================================
router = DefaultRouter()

# Guardians ViewSet
router.register(r'guardians', GuardianViewSet, basename='guardian')
# Gera automaticamente:
# - GET    /api/v1/contacts/guardians/           -> list() - Lista paginada
# - GET    /api/v1/contacts/guardians/{id}/      -> retrieve() - Detalhes + boletos
# - GET    /api/v1/contacts/guardians/{id}/invoices/ -> invoices() - Apenas boletos


urlpatterns = [
    # ===================================================================
    # ✅ NOVA ARQUITETURA (USAR ESTES ENDPOINTS)
    # ===================================================================
    path('', include(router.urls)),

    # Endpoint de boletos globais (todos alunos da escola)
    # Mantido pois não conflita com a nova arquitetura
    path(
        'students/invoices/',
        StudentInvoiceView.as_view(),
        name='student-invoices'
    ),

    # ===================================================================
    # ⚠️ DEPRECATED - ENDPOINTS ANTIGOS (REMOVER APÓS MIGRAÇÃO)
    # ===================================================================
    # Estes endpoints serão removidos quando frontend migrar 100%

    # Endpoint antigo: GET /api/v1/contacts/guardians-old/
    # ➡️ Migrar para: GET /api/v1/contacts/guardians/
    path(
        'guardians-old/',
        StudentsGuardiansView.as_view(),
        name='guardians-old'
    ),

    # Endpoint antigo: GET /api/v1/contacts/students/guardians-old/
    # ➡️ Migrar para: GET /api/v1/contacts/guardians/
    path(
        'students/guardians-old/',
        StudentGuardianView.as_view(),
        name='student-guardians-old'
    ),
]

# ===================================================================
# 📚 DOCUMENTAÇÃO DOS ENDPOINTS
# ===================================================================
"""
ENDPOINTS DISPONÍVEIS
=====================

✅ NOVA ARQUITETURA (RECOMENDADO)
----------------------------------

1. Lista Guardians (paginada)
   GET /api/v1/contacts/guardians/

   Query params:
   - search: Busca por nome, CPF, email, nome do filho
   - cpf: Filtro exato por CPF
   - ordering: nome ou -nome
   - page: Número da página
   - page_size: Itens por página (max: 100)

   Response:
   {
     "count": 150,
     "next": "http://...",
     "previous": null,
     "results": [
       {
         "id": 680,
         "nome": "Maria Silva",
         "cpf": "123.456.789-00",
         "email": "maria@email.com",
         "telefone": "11999999999",
         "total_filhos": 2,
         "filhos_nomes": ["João", "Ana"]
       }
     ]
   }

2. Detalhes Guardian (completo com boletos)
   GET /api/v1/contacts/guardians/{id}/

   Response:
   {
     "id": 680,
     "nome": "Maria Silva",
     "cpf": "123.456.789-00",
     "endereco": {...},
     "filhos": [
       {
         "id": 14022,
         "nome": "João Pedro",
         "turma": "8E - Tarde",
         "boletos": [...],
         "resumo_boletos": {
           "total": 12,
           "pagos": 8,
           "valor_pendente": 2550.00
         }
       }
     ],
     "resumo_geral_boletos": {
       "total_filhos": 2,
       "total_boletos": 24,
       "pagos": 16,
       "valor_pendente": 5100.00
     }
   }

3. Apenas Boletos de um Guardian
   GET /api/v1/contacts/guardians/{id}/invoices/

   Response:
   {
     "guardian_id": 680,
     "guardian_name": "Maria Silva",
     "total_filhos": 2,
     "resumo_geral": {...},
     "filhos": [...]
   }

4. Boletos de TODOS os alunos da escola
   GET /api/v1/contacts/students/invoices/

   (Mantido - não conflita com nova arquitetura)


⚠️ DEPRECATED (NÃO USAR - SERÁ REMOVIDO)
----------------------------------------

GET /api/v1/contacts/guardians-old/
GET /api/v1/contacts/students/guardians-old/

➡️ Migrar para: GET /api/v1/contacts/guardians/


CACHE STRATEGY
==============

Nível 1 (1h):   Dados SIGA globais (guardians, students)
Nível 2 (6h):   Guardian detalhado
Nível 3 (30min): Boletos
Nível 4 (15min): Buscas

Cache automático gerenciado por SigaCacheManager.


PERMISSÕES
==========

Todos os endpoints: IsSchoolStaff (managers e operators)
"""