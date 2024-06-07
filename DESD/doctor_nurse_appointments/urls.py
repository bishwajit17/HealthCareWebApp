from django.urls import path
from . import views

app_name = 'doctor_nurse_appointments'

urlpatterns = [
    path('', views.appointments_list, name="appointments_list"),
    path('amend_booking_handling/', views.amend_booking_handling, name="amend_booking_handling"),
    path('amend_booking/', views.amend_booking, name="amend_booking"),
    path('cancel_appointment', views.cancel_appointment, name='cancel_appointment'),
    path('amend_confirmation_handling/', views.amend_confirmation_handling, name='amend_confirmation_handling'),
    path('cancel_reason/', views.cancel_reason, name='cancel_reason'),
    path('forward_detail/', views.forward_detail, name='forward_detail'),
    path('forward_appointment/', views.forward_appointment, name='forward_appointment'),
    path('prescribe_appointment/', views.prescribe_appointment, name='prescribe_appointment'),
    # path('clear_amend_item/', views.clear_amend_item, name="clear_amend_item"),
]