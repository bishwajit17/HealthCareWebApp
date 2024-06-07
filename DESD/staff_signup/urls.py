from django.urls import path
from . import views

urlpatterns = [
    path('staffDetail/', views.staffDetail, name='staffDetail'),
    path('staff_signup/', views.staff_signup, name='staff_signup'),
    path('staffDetail/deleteStaff/', views.deleteStaff, name='deleteStaff'),
    path('staffDetail/editStaff/<int:user_id>/<str:dates>/', views.editStaff, name='editStaff'),
    path('extract_data_csv/', views.extract_data_csv, name='extract_data_csv'),

]