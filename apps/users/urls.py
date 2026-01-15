# ===================================================================
# apps/users/urls.py - CORRIGIDO
# ===================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CORRETO: Usa UserViewSet que existe em views.py
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Autenticação
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # Perfil do usuário autenticado
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),

    # Router
    path('', include(router.urls)),
]
