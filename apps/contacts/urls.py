# apps/contacts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('students/guardians/', views.StudentGuardianView.as_view(), name='student-guardians'),
    path('students/invoices/', views.StudentInvoiceView.as_view(), name='student-invoices'),
]
