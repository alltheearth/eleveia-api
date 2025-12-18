"""conftest.py - na raiz do projeto"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    """Cliente API para testes"""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Cliente autenticado"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def superuser():
    """Cria um superusuário"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )


@pytest.fixture
def user():
    """Cria um usuário comum"""
    return User.objects.create_user(
        username='testuser',
        email='user@test.com',
        password='test123'
    )


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Permite acesso ao DB em todos os testes"""
    pass
