from django.urls import path
from . import views

urlpatterns = [
    path('', views.patients_prescription_view, name='patients_prescription'),
    path('prescription_invoice/', views.prescription_invoice_view, name='prescription_invoice'),
    path('prescription_cancelled_desc/', views.prescription_cancellation_desc_view, name='prescription_cancelled_desc'),
    path('handle_prescription_request/', views.handle_prescription_request, name='handle_prescription_request'),
]
