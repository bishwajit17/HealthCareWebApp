from django.urls import path
from . import views

urlpatterns = [
    path('', views.patients_dashboard_view, name='patient_main'),
]
