# ===================================================================
# apps/users/urls.py - VERSÃO CORRIGIDA
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')

urlpatterns = [
    # Autenticação (function-based views)
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # Perfil do usuário autenticado
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),

    # ViewSets (usuarios e perfis)
    path('', include(router.urls)),
]