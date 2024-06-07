from django.urls import path
from . import views

app_name = 'patients_appointments'

urlpatterns = [
    path('', views.new_booking, name="booking"),
    path('fetch_calendar', views.fetch_calendar, name='fetch_calendar'),
    path('slot_selection_handling/', views.slot_selection_handling, name="slot_selection_handling"),
    path('patient_slot_confirmation/', views.patient_slot_confirmation, name="patient_slot_confirmation"),
    path('slot_confirmation_handling/', views.slot_confirmation_handling, name='slot_confirmation_handling'),
    path('patient_appointment_confirm/', views.patient_appointment_confirm, name='patient_appointment_confirm'),
    path('patient_appointment_fail/', views.patient_appointment_fail, name='patient_appointment_fail'),
    path('patient_appointments_list/', views.patient_appointments_list, name='patient_appointments_list'),
    path('patient_appointments_invoice/', views.patient_appointments_invoice, name="patient_appointments_invoice"),
    path('clear_amend_item/', views.clear_amend_item, name="clear_amend_item"),
    path('cancel_appointment', views.cancel_appointment, name='cancel_appointment'),
    path('patient_appointments_reason', views.patient_appointments_reason, name='patient_appointments_reason'),
]