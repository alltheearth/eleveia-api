"""core/tests/base.py"""
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class BaseTestCase(TestCase):
    """Classe base para testes unitários"""

    @classmethod
    def setUpTestData(cls):
        """Setup executado uma vez por classe de teste"""
        cls.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

    def setUp(self):
        """Setup executado antes de cada teste"""
        pass

    def tearDown(self):
        """Cleanup executado após cada teste"""
        pass


class BaseAPITestCase(APITestCase):
    """Classe base para testes de API"""

    @classmethod
    def setUpTestData(cls):
        """Setup para testes de API"""
        cls.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

    def authenticate(self, user=None):
        """Helper para autenticar cliente"""
        user = user or self.superuser
        self.client.force_authenticate(user=user)

    def create_user(self, **kwargs):
        """Helper para criar usuários"""
        defaults = {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'test123'
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
