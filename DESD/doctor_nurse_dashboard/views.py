from django.shortcuts import render, redirect
from database_models.models import PrescriptionsAssignments
from DESD.views import verify_user_role

"""
Checks if the patient has any prescriptions with collection_status = 'awaiting decision'.
Returns True if at least one prescription is found, otherwise returns False.
"""
def check_awaiting_decision_prescriptions():
    return PrescriptionsAssignments.objects.filter(collection_status='awaiting decision').exists()

"""
Renders the main page for doctor/nurse, passes the user data and the presecription notification as context.
"""
def doctor_nurse_dashboard_view(request):
    user_data = request.session.get('user_data')
    if not verify_user_role(user_data.get('role'), ['doctor', 'nurse']):
        return redirect('/')
        
    context = {
        'user_data': user_data,
        'new_prescriptions_status': check_awaiting_decision_prescriptions(),
    }

    return render(request, 'doctor_nurse_dashboard.html', context)
