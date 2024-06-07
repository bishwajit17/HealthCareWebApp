from django.http import  JsonResponse
from django.shortcuts import redirect

"""
Function to check if session is expired or not
Returns 'True' if session is active else 'False'
"""
def check_session_data(request):
    session_data = request.session.get('user_data')
    # print('session_data', session_data)
    if session_data:
        return JsonResponse({'session_data': True})
    else:
        return JsonResponse({'session_data': False})

"""
Function to verify user role
"""
def verify_user_role(user_role, page_role):
    if user_role in page_role:
        return True
    else:
        return False