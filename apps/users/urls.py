# ===================================================================
# apps/users/urls.py - VERSÃO COMPLETA E ORGANIZADA
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ===================================================================
# ROUTER PARA VIEWSETS
# ===================================================================
router = DefaultRouter()

# 👥 Gerenciamento de usuários (managers/superusers)
router.register(r'users', views.UserViewSet, basename='user')

# 🎭 Gerenciamento de perfis (managers/superusers)
router.register(r'profiles', views.UserProfileViewSet, basename='profile')

# ===================================================================
# URL PATTERNS - Organizado por Categoria
# ===================================================================
urlpatterns = [
    # ===============================================================
    # 🔐 AUTENTICAÇÃO (Público)
    # ===============================================================
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # ===============================================================
    # 👤 PERFIL DO USUÁRIO AUTENTICADO
    # ===============================================================
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('profile/change-password/', views.change_password, name='change-password'),

    # ===============================================================
    # 👥 VIEWSETS (Gerenciamento de Usuários e Perfis)
    # ===============================================================
    # Registra todas as rotas dos ViewSets:
    #
    # UserViewSet:
    # - GET    /users/          - Lista usuários da escola
    # - GET    /users/{id}/     - Detalhes de um usuário
    # - POST   /users/          - Cria usuário (managers)
    # - PATCH  /users/{id}/     - Atualiza usuário (managers)
    # - DELETE /users/{id}/     - Remove usuário (managers)
    # - GET    /users/me/       - Usuário autenticado
    # - GET    /users/stats/    - Estatísticas (managers)
    #
    # UserProfileViewSet:
    # - GET    /profiles/                    - Lista perfis
    # - GET    /profiles/{id}/               - Detalhes de um perfil
    # - POST   /profiles/                    - Cria perfil (managers)
    # - PATCH  /profiles/{id}/               - Atualiza perfil
    # - DELETE /profiles/{id}/               - Remove perfil (managers)
    # - GET    /profiles/me/                 - Perfil autenticado
    # - GET    /profiles/school_users/       - Usuários da escola (managers)
    # - PATCH  /profiles/{id}/toggle_active/ - Ativa/desativa perfil (managers)
    # - PATCH  /profiles/{id}/change_role/   - Altera role (managers)
    path('', include(router.urls)),
]

# ===================================================================
# 📚 DOCUMENTAÇÃO DAS ROTAS
# ===================================================================
"""
ESTRUTURA COMPLETA DA API DE USUÁRIOS
======================================

BASE URL: /api/v1/auth/

┌─────────────────────────────────────────────────────────────────┐
│ 🔐 AUTENTICAÇÃO (Público - AllowAny)                            │
├─────────────────────────────────────────────────────────────────┤
│ POST   /register/               - Registrar novo usuário        │
│ POST   /login/                  - Login (retorna token)         │
│ POST   /logout/                 - Logout (deleta token)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 👤 PERFIL DO USUÁRIO AUTENTICADO (IsAuthenticated)             │
├─────────────────────────────────────────────────────────────────┤
│ GET    /profile/                - Ver perfil completo           │
│ PATCH  /profile/update/         - Atualizar dados básicos       │
│ POST   /profile/change-password/- Alterar senha                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 👥 GERENCIAMENTO DE USUÁRIOS (IsAuthenticated/IsManager)       │
├─────────────────────────────────────────────────────────────────┤
│ GET    /users/                  - Lista usuários da escola      │
│ GET    /users/{id}/             - Detalhes de usuário           │
│ POST   /users/                  - Criar usuário (managers)      │
│ PATCH  /users/{id}/             - Atualizar usuário (managers)  │
│ DELETE /users/{id}/             - Deletar usuário (managers)    │
│ GET    /users/me/               - Dados do próprio usuário      │
│ GET    /users/stats/            - Estatísticas (managers)       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🎭 GERENCIAMENTO DE PERFIS (IsAuthenticated/IsManager)         │
├─────────────────────────────────────────────────────────────────┤
│ GET    /profiles/               - Lista perfis da escola        │
│ GET    /profiles/{id}/          - Detalhes de perfil            │
│ POST   /profiles/               - Criar perfil (managers)       │
│ PATCH  /profiles/{id}/          - Atualizar perfil              │
│ DELETE /profiles/{id}/          - Deletar perfil (managers)     │
│ GET    /profiles/me/            - Perfil do próprio usuário     │
│ GET    /profiles/school_users/  - Usuários da escola (managers) │
│ PATCH  /profiles/{id}/toggle_active/ - Ativar/desativar        │
│ PATCH  /profiles/{id}/change_role/   - Alterar role (managers) │
└─────────────────────────────────────────────────────────────────┘


🔒 NÍVEIS DE PERMISSÃO
======================

1️⃣ AllowAny (Público)
   - /register/
   - /login/

2️⃣ IsAuthenticated (Usuário logado)
   - /logout/
   - /profile/
   - /profile/update/
   - /profile/change-password/
   - /users/ (list/retrieve apenas da própria escola)
   - /profiles/ (list/retrieve apenas da própria escola)

3️⃣ IsManager (Gestores da escola)
   - /users/ (create/update/delete)
   - /users/stats/
   - /profiles/ (create/delete)
   - /profiles/school_users/
   - /profiles/{id}/toggle_active/
   - /profiles/{id}/change_role/

4️⃣ Superuser (Administradores do sistema)
   - Acesso total a todos os endpoints
   - Pode gerenciar qualquer escola


📊 FILTROS E BUSCAS
===================

UserViewSet (/users/):
  - ?is_active=true
  - ?profile__role=manager
  - ?profile__is_active=true
  - ?search=username ou email
  - ?ordering=username ou -date_joined

UserProfileViewSet (/profiles/):
  - ?role=manager
  - ?is_active=true
  - ?school=1
  - ?search=username ou email
  - ?ordering=created_at ou -created_at


🎯 EXEMPLOS DE USO
==================

1️⃣ Registro de usuário:
POST /api/v1/auth/register/
{
    "username": "joao",
    "email": "joao@escola.com",
    "password": "senha123",
    "password2": "senha123",
    "school_id": 1,
    "role": "operator"
}

2️⃣ Login:
POST /api/v1/auth/login/
{
    "username": "joao",
    "password": "senha123"
}
→ Retorna: {"token": "abc123...", "user": {...}}

3️⃣ Ver perfil:
GET /api/v1/auth/profile/
Header: Authorization: Token abc123...

4️⃣ Listar usuários da escola:
GET /api/v1/auth/users/
Header: Authorization: Token abc123...

5️⃣ Alterar role de usuário (manager):
PATCH /api/v1/auth/profiles/5/change_role/
Header: Authorization: Token abc123...
{
    "role": "manager"
}

6️⃣ Ver estatísticas (manager):
GET /api/v1/auth/users/stats/
Header: Authorization: Token abc123...
"""