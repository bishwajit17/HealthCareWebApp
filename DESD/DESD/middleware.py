# middleware.py
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import logout

"""
Function to handle session timeout after timer has surpassed session time limit.
"""
class SessionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path_info.lstrip('/')
        
        if not request.session.get('user_data') and path not in settings.SESSION_EXEMPT_PATHS:
            logout(request)
            print('expired session')
            return redirect('/?session_expired=true')
        
        return response
