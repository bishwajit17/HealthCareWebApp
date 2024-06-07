from django.urls import path
from . import views

urlpatterns = [
    path('patientDetails/', views.patientDetails, name='patientDetails'),
    path('patient_signup/', views.patient_signup, name='patient_signup'),
    path('patientDetails/deletePatient/', views.deletePatient, name='deletePatient'),
    path('patientDetails/editPatient/<int:user_id>/<str:dates>/', views.editPatient, name='editPatient'),
    path('extract_data/', views.extract_data, name='extract_data'),
]