from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('update_record/', views.update_record, name='update_record'),
    path('delete/', views.delete, name='delete'),
    path('goback/', views.goback, name='goback'),    
    path('extract_data_csv/', views.extract_data_csv, name='extract_data_csv'),
    path('update_record/goback/', views.goback, name='goback'),
]
