# apps/contacts/urls.py
from django.urls import path
from . import views
from .views.guardian_views import StudentGuardianView

urlpatterns = [
    path('students/guardians/', views.StudentGuardianView.as_view(), name='student-guardians'),
    path('students/invoices/', views.StudentInvoiceView.as_view(), name='student-invoices'),
    path(
        'guardians/',
        StudentGuardianView.as_view(),
        name='guardian-list'
    ),
]