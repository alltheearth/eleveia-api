# apps/contacts/urls.py
"""
URLs do app Contacts

ROTAS DISPONÍVEIS:
- /students/guardians/  - Dados de responsáveis por aluno
- /students/invoices/   - Boletos de todos os alunos
- /guardians/           - Lista de responsáveis
- /dashboard/           - Dashboard com métricas gerais (NOVO)
"""

from django.urls import path
from .views.guardian_views import StudentsGuardiansView
from .views.student_invoice_views import StudentInvoiceView
from .views.student_guardian_views import StudentGuardianView
from .views.dashboard_views import SchoolDashboardView  # NOVO

urlpatterns = [
    # Dados de alunos e responsáveis
    path('students/guardians/', StudentGuardianView.as_view(), name='student-guardians'),

    # Boletos
    path('students/invoices/', StudentInvoiceView.as_view(), name='student-invoices'),

    # Responsáveis
    path(
        'guardians/',
        StudentsGuardiansView.as_view(),
        name='guardian-list'
    ),

    # Dashboard/Métricas (NOVO)
    path(
        'dashboard/',
        SchoolDashboardView.as_view(),
        name='school-dashboard'
    ),
]