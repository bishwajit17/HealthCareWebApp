"""
URL configuration for DESD project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    
Add an import:  from my_app import views
Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    
Add an import:  from other_app.views import Home
Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    
Import the include() function: from django.urls import include, path
Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from . import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('check_session_data/', views.check_session_data, name='check_session_data'),
    path('', include('login_page.urls'), name='login_page'),
    path('', include('sign_up.urls'), name='signup'),
    path('account_settings/', include('account_settings.urls')),
    path('admin_payments/', include('admin_payments.urls')),
    path('admin_reports/', include('admin_reports.urls')),
    path('admin_staffrates/', include('admin_staffrates.urls')),
    path('admin_appointments/', include('admin_appointments.urls', namespace='appointment_appointments')),
    path('booking/', include("patients_appointments.urls", namespace='booking')),
    path('patient_main/', include("patients_dashboard.urls")),
    path('patient_prescription/', include("patients_prescription.urls"), name='patients_prescription'),
    path('doctor_nurse_main/', include("doctor_nurse_dashboard.urls"), name='doctor_nurse_main'),
    path('doctor_nurse_prescriptions/', include("doctor_nurse_prescriptions.urls"), name='doctor_nurse_prescriptions'),
    path('doctor_nurse_appointments/', include("doctor_nurse_appointments.urls", namespace='doctor_nurse_appointments')),
    path('admin_main/', include("admins_dashboard.urls"), name='admin_main'),
    path('', include('staff_signup.urls'), name='staff_signup'),
    path('', include('patient_signup.urls'), name='patient_signup'),
]
