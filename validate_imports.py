# validate_imports.py
import os
import sys


def check_imports():
    """Verifica se todos os imports estão corretos"""

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    try:
        import django
        django.setup()

        print("✅ Django configurado")

        # Testar imports de users
        from apps.users.models import PerfilUsuario
        from apps.users.serializers import UsuarioSerializer
        from apps.users.views import login
        print("✅ Users OK")

        # Testar imports de schools
        from apps.schools.models import Escola
        from apps.schools.serializers import EscolaSerializer
        from apps.schools.views import EscolaViewSet
        print("✅ Schools OK")

        # Testar imports de contacts
        from apps.contacts.models import Contato
        from apps.contacts.views import ContatoViewSet
        print("✅ Contacts OK")

        # Testar imports de events
        from apps.events.models import CalendarioEvento
        from apps.events.views import CalendarioEventoViewSet
        print("✅ Events OK")

        # Testar imports de faqs
        from apps.faqs.models import FAQ
        from apps.faqs.views import FAQViewSet
        print("✅ FAQs OK")

        # Testar imports de documents
        from apps.documents.models import Documento
        from apps.documents.views import DocumentoViewSet
        print("✅ Documents OK")

        # Testar imports de dashboard
        from apps.dashboard.models import Dashboard
        from apps.dashboard.views import DashboardViewSet
        print("✅ Dashboard OK")

        # Testar core
        from core.permissions import EscolaPermission
        from core.mixins import UsuarioEscolaMixin
        print("✅ Core OK")

        print("\n🎉 TODOS OS IMPORTS ESTÃO CORRETOS!")
        return True

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = check_imports()
    sys.exit(0 if success else 1)