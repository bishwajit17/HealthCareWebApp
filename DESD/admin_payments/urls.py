from django.urls import path
from . import views

urlpatterns = [    
    path('', views.admin_payment, name='admin_payment'),
    path('payments_extract_data/', views.payments_extract_data, name='payments_extract_data'),
    path('presc_mark_paid/<int:id>', views.presc_mark_paid, name='presc_mark_paid'),
    path('appoint_mark_paid/<int:id>', views.appoint_mark_paid, name='appoint_mark_paid'),
    path('appoint_mark_all_paid/', views.appoint_mark_all_paid, name='appoint_mark_all_paid'),
    path('presc_mark_all_paid/', views.presc_mark_all_paid, name='presc_mark_all_paid'),
]
