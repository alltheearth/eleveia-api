# ===================================================================
# apps/storage/tests/factories.py
# ===================================================================
import uuid
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User

from apps.schools.models import School
from apps.users.models import UserProfile
from apps.storage.models import StorageFile


# ------------------------------------------------------------------
# School
# ------------------------------------------------------------------

class SchoolFactory(DjangoModelFactory):
    class Meta:
        model = School

    school_name = factory.Sequence(lambda n: f'Escola {n}')
    tax_id = factory.Sequence(lambda n: f'{n:014d}')
    phone = '11999999999'
    email = factory.LazyAttribute(lambda o: f'{o.school_name.replace(" ", "").lower()}@test.com')
    postal_code = '01000-000'
    street_address = 'Rua Teste'
    city = 'São Paulo'
    state = 'SP'


# ------------------------------------------------------------------
# User + Profile
# ------------------------------------------------------------------

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@test.com')
    password = factory.LazyFunction(lambda: 'senha123!')

    class Params:
        # Use: UserFactory(superuser=True)
        superuser = factory.Trait(is_superuser=True, is_staff=True)


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    school = factory.SubFactory(SchoolFactory)
    role = 'operator'
    is_active = True

    class Params:
        manager = factory.Trait(role='manager')
        end_user = factory.Trait(role='end_user')


# ------------------------------------------------------------------
# StorageFile (arquivo e pasta)
# ------------------------------------------------------------------

class StorageFileFactory(DjangoModelFactory):
    class Meta:
        model = StorageFile

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    name = factory.Sequence(lambda n: f'arquivo_{n}.pdf')
    size = 1024
    mime_type = 'application/pdf'
    extension = 'pdf'
    r2_key = factory.LazyFunction(lambda: f'uploads/{uuid.uuid4()}.pdf')
    r2_bucket = 'test-bucket'
    parent_folder = None
    is_folder = False
    created_by = factory.SubFactory(UserFactory)


class StorageFolderFactory(StorageFileFactory):
    """Cria pastas virtuais (sem chave R2)."""
    name = factory.Sequence(lambda n: f'pasta_{n}')
    size = 0
    mime_type = 'application/folder'
    extension = ''
    r2_key = ''
    r2_bucket = ''
    is_folder = True