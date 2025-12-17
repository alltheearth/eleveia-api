"""
URLs do app de usuários
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')

urlpatterns = [
    # Autenticação
    path('registro/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('atualizar-perfil/', views.atualizar_perfil, name='atualizar-perfil'),

    # Router
    path('', include(router.urls)),
]