# apps/contacts/urls.py
from django.urls import path
from .views.guardian_views import StudentsGuardiansView
from .views.student_invoice_views import StudentInvoiceView
from .views.student_guardian_views import StudentGuardianView

urlpatterns = [
    path('students/guardians/', StudentGuardianView.as_view(), name='student-guardians'),
    path('students/invoices/', StudentInvoiceView.as_view(), name='student-invoices'),
    path(
        'guardians/',
        StudentsGuardiansView.as_view(),
        name='guardian-list'
    ),
]