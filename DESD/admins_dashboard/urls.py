from django.urls import path
from . import views

urlpatterns = [
    path('', views.admins_dashboard_view, name='admin_main'),
]
