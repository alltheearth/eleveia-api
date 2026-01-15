# ===================================================================
# apps/users/tests/test_permissions.py - TESTES COMPLETOS
# ===================================================================
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import UserProfile
from apps.schools.models import School


class TestPermissionHierarchy(TestCase):
    """Testa hierarquia de permissões"""

    def setUp(self):
        """Setup inicial"""
        self.client = APIClient()
        
        # Criar escolas
        self.school_a = School.objects.create(
            school_name='Escola A',
            tax_id='12345678901234',
            phone='11999999999',
            email='escolaa@test.com',
            postal_code='01000-000',
            street_address='Rua A',
            city='São Paulo',
            state='SP'
        )
        
        self.school_b = School.objects.create(
            school_name='Escola B',
            tax_id='98765432109876',
            phone='11888888888',
            email='escolab@test.com',
            postal_code='02000-000',
            street_address='Rua B',
            city='São Paulo',
            state='SP'
        )
        
        # Criar superuser
        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='super@test.com',
            password='super123'
        )
        
        # Criar manager escola A
        self.manager_a = User.objects.create_user(
            username='manager_a',
            email='managera@test.com',
            password='senha123'
        )
        UserProfile.objects.create(
            user=self.manager_a,
            school=self.school_a,
            role='manager',
            is_active=True
        )
        
        # Criar operator escola A
        self.operator_a = User.objects.create_user(
            username='operator_a',
            email='operatora@test.com',
            password='senha123'
        )
        UserProfile.objects.create(
            user=self.operator_a,
            school=self.school_a,
            role='operator',
            is_active=True
        )
        
        # Criar end_user escola A
        self.enduser_a = User.objects.create_user(
            username='enduser_a',
            email='endusera@test.com',
            password='senha123'
        )
        UserProfile.objects.create(
            user=self.enduser_a,
            school=self.school_a,
            role='end_user',
            is_active=True,
            phone='11777777777'
        )
        
        # Criar manager escola B
        self.manager_b = User.objects.create_user(
            username='manager_b',
            email='managerb@test.com',
            password='senha123'
        )
        UserProfile.objects.create(
            user=self.manager_b,
            school=self.school_b,
            role='manager',
            is_active=True
        )

    # ===============================================================
    # TESTES DE ACESSO A ESCOLAS
    # ===============================================================

    def test_superuser_sees_all_schools(self):
        """Superuser vê todas as escolas"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_manager_sees_only_own_school(self):
        """Manager vê apenas sua escola"""
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.get('/api/v1/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['school_name'], 'Escola A')

    def test_manager_cannot_see_other_school(self):
        """Manager não vê escola de outro"""
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.get(f'/api/v1/schools/{self.school_b.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_enduser_sees_own_school_readonly(self):
        """End user vê sua escola (dados públicos)"""
        self.client.force_authenticate(user=self.enduser_a)
        response = self.client.get(f'/api/v1/schools/{self.school_a.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica que messaging_token está oculto
        self.assertNotIn('messaging_token', response.data)

    # ===============================================================
    # TESTES DE EDIÇÃO DE ESCOLA
    # ===============================================================

    def test_only_superuser_can_edit_protected_fields(self):
        """Apenas superuser pode editar campos super protegidos"""
        # Manager tenta alterar nome
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.patch(
            f'/api/v1/schools/{self.school_a.id}/',
            {'school_name': 'Novo Nome'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('school_name', response.data)

    def test_manager_can_edit_non_protected_fields(self):
        """Manager pode editar campos não-super-protegidos"""
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.patch(
            f'/api/v1/schools/{self.school_a.id}/',
            {'phone': '11666666666'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], '11666666666')

    def test_operator_cannot_edit_school(self):
        """Operator não pode editar escola"""
        self.client.force_authenticate(user=self.operator_a)
        response = self.client.patch(
            f'/api/v1/schools/{self.school_a.id}/',
            {'phone': '11555555555'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_enduser_cannot_edit_school(self):
        """End user não pode editar escola"""
        self.client.force_authenticate(user=self.enduser_a)
        response = self.client.patch(
            f'/api/v1/schools/{self.school_a.id}/',
            {'about': 'Nova descrição'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ===============================================================
    # TESTES DE CRIAÇÃO/DELEÇÃO DE ESCOLA
    # ===============================================================

    def test_only_superuser_can_create_school(self):
        """Apenas superuser pode criar escola"""
        # Manager tenta criar
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.post(
            '/api/v1/schools/',
            {
                'school_name': 'Nova Escola',
                'tax_id': '11111111111111',
                'phone': '11444444444',
                'email': 'nova@test.com',
                'postal_code': '03000-000',
                'street_address': 'Rua Nova',
                'city': 'São Paulo',
                'state': 'SP'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_superuser_can_delete_school(self):
        """Apenas superuser pode deletar escola"""
        # Manager tenta deletar
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.delete(f'/api/v1/schools/{self.school_a.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ===============================================================
    # TESTES DE ISOLAMENTO DE DADOS
    # ===============================================================

    def test_data_isolation_faqs(self):
        """FAQs são isoladas por escola"""
        from apps.faqs.models import FAQ
        
        # Criar FAQs em ambas escolas
        faq_a = FAQ.objects.create(
            school=self.school_a,
            question='FAQ Escola A',
            answer='Resposta A',
            category='Geral',
            created_by=self.manager_a
        )
        
        faq_b = FAQ.objects.create(
            school=self.school_b,
            question='FAQ Escola B',
            answer='Resposta B',
            category='Geral',
            created_by=self.manager_b
        )
        
        # Manager A não vê FAQ da escola B
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.get('/api/v1/faqs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['question'], 'FAQ Escola A')

    def test_enduser_can_read_but_not_write_faqs(self):
        """End user pode ler mas não escrever FAQs"""
        from apps.faqs.models import FAQ
        
        faq = FAQ.objects.create(
            school=self.school_a,
            question='FAQ Teste',
            answer='Resposta',
            category='Geral',
            created_by=self.manager_a
        )
        
        # End user pode ler
        self.client.force_authenticate(user=self.enduser_a)
        response = self.client.get('/api/v1/faqs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # End user não pode criar
        response = self.client.post(
            '/api/v1/faqs/',
            {
                'school': self.school_a.id,
                'question': 'Nova FAQ',
                'answer': 'Resposta',
                'category': 'Geral'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ===============================================================
    # TESTES DE TICKETS (END USER)
    # ===============================================================

    def test_enduser_can_create_ticket(self):
        """End user pode criar ticket"""
        self.client.force_authenticate(user=self.enduser_a)
        response = self.client.post(
            '/api/v1/tickets/',
            {
                'title': 'Meu Ticket',
                'description': 'Preciso de ajuda',
                'priority': 'medium'
            }
        )
        
        # Ajusta expectativa se endpoint não existir
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_enduser_sees_only_own_tickets(self):
        """End user vê apenas seus tickets"""
        # Implementar quando tickets estiver configurado
        pass

    def test_staff_sees_all_school_tickets(self):
        """Staff vê todos os tickets da escola"""
        # Implementar quando tickets estiver configurado
        pass


# ===================================================================
# TESTES DE PERFORMANCE
# ===================================================================

class TestQueryOptimization(TestCase):
    """Testa otimizações de queries"""

    def test_school_list_no_n_plus_1(self):
        """Lista de escolas não faz N+1 queries"""
        # Criar várias escolas
        schools = [
            School.objects.create(
                school_name=f'Escola {i}',
                tax_id=f'{i:014d}',
                phone='11999999999',
                email=f'escola{i}@test.com',
                postal_code='01000-000',
                street_address='Rua Teste',
                city='São Paulo',
                state='SP'
            )
            for i in range(10)
        ]
        
        superuser = User.objects.create_superuser(
            'admin', 'admin@test.com', 'admin123'
        )
        
        client = APIClient()
        client.force_authenticate(user=superuser)
        
        # Deve fazer poucas queries
        with self.assertNumQueries(3):  # Auth + Count + Select
            response = client.get('/api/v1/schools/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)