from django.urls import path
from . import views
# from patients_appointments import views as appointment_views

urlpatterns = [
    path('', views.doctor_nurse_prescription_view, name='doctor_nurse_prescriptions'),
    path('handle_prescription_cancellation/', views.handle_prescription_cancellation, name='handle_prescription_cancellation'),
    path('handle_prescription_approval/', views.handle_prescription_approval, name='handle_prescription_approval'),
    path('view_cancellation_reason/', views.prescription_cancellation_reason_view, name='view_cancellation_reason'),
    path('view_prescription_invoice/', views.prescription_invoice_view, name='view_prescription_invoice'),
    path('handle_mark_collected/', views.handle_mark_collected, name='handle_mark_collected'),
    path('collected_and_cancelled_list/', views.get_collected_and_cancelled_prescription_list, name='collected_and_cancelled_list'),
    path('awaiting_decision_list/', views.get_awaiting_decision_prescription_list, name='awaiting_decision_list'),
    path('waiting_to_collect_list/', views.get_waiting_to_collect_prescription_list, name='waiting_to_collect_list'),
]
