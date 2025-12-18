"""apps/users/tests/factories.py"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from apps.users.models import PerfilUsuario
from apps.schools.models import Escola


class EscolaFactory(DjangoModelFactory):
    """Factory para Escola"""

    class Meta:
        model = Escola

    nome_escola = factory.Faker('company')
    cnpj = factory.Sequence(lambda n: f'{n:014d}')
    telefone = factory.Faker('phone_number')
    email = factory.Faker('email')
    cep = factory.Faker('postcode')
    endereco = factory.Faker('street_address')
    cidade = factory.Faker('city')
    estado = 'SP'


class UserFactory(DjangoModelFactory):
    """Factory para User"""

    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('test123')


class PerfilUsuarioFactory(DjangoModelFactory):
    """Factory para PerfilUsuario"""

    class Meta:
        model = PerfilUsuario

    usuario = factory.SubFactory(UserFactory)
    escola = factory.SubFactory(EscolaFactory)
    tipo = 'operador'
    ativo = True


class GestorFactory(PerfilUsuarioFactory):
    """Factory para criar Gestor"""
    tipo = 'gestor'

