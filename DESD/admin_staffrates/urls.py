from django.urls import path
from . import views

urlpatterns = [    
    path('', views.admin_staffrate, name='admin_staffrate'),
    #path('delete_staff_rate/<int:staff_rate_id>/', views.delete_staff_rate, name='delete_staff_rate'),
    path('edit_staff_rate/<int:staff_rate_id>/', views.edit_staff_rate, name='edit_staff_rate'),

]
