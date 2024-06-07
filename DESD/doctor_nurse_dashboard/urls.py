from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_nurse_dashboard_view, name='doctor_nurse_main'),
]
