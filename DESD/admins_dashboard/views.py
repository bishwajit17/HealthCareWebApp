from django.shortcuts import render, redirect
from DESD.views import verify_user_role

"""
Renders the main page for admins, passes the user data as context. 
"""
def admins_dashboard_view(request):
    user_data = request.session.get('user_data')
    if not verify_user_role(user_data.get('role'), 'admin'):
        return redirect('/')

    context = {
        'user_data': user_data,
    }

    return render(request, 'admins_dashboard.html', context)

"""
Renders the signup page for admins.
"""
def staffsignup(request):
    response = render(request,'staffSignUpPage.html')
    return response