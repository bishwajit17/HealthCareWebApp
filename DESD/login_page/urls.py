from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login_page'),
    path('login/', views.user_login, name='user_login'),
    # path('signup_page/', views.signup_page, name='signup_page'),
]
