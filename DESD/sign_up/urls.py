from django.urls import path
from . import views

urlpatterns = [
    path('signup_page/', views.user_signup, name='user_signup'),
]
