from django.urls import path
from . import views

app_name = 'admin_appointments'

urlpatterns = [
    path('', views.appointment_details, name="appointment_details"),
    path('update_list/', views.update_list, name='update_list'),
    path('cancel_appointment', views.cancel_appointment, name='cancel_appointment'),
    path('appointment_invoice', views.appointment_invoice, name="appointment_invoice"),
    path('appointment_reason', views.appointment_reason, name='appointment_reason'),
]