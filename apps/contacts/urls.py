# apps/contacts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, views_new

router = DefaultRouter()
# ✅ ViewSets (como o WhatsAppContactViewSet) permanecem no router
router.register(r'whatsapp', views.WhatsAppContactViewSet, basename='contact')

urlpatterns = [
    # ✅ Rotas automáticas do router
    path('', include(router.urls)),

    # ✅ Rotas manuais para APIViews (StudentGuardianView)
    # Note que ela fica FORA do router.register
    path('students/<int:student_id>/guardians/', views_new.StudentGuardianView.as_view(), name='student-guardians'),
    path('students/<int:student_id>/invoices/', views_new.StudentInvoiceView.as_view())
]
