from django.shortcuts import render, redirect
from database_models.models import PrescriptionsAssignments
from DESD.views import verify_user_role

"""
Checks if the patient has any prescriptions with collection_status = 'waiting to collect'.
Returns True if at least one prescription is found, otherwise returns False.
"""
def check_not_collected_prescriptions(patient_id):
    return PrescriptionsAssignments.objects.filter(appointment__patient_id=patient_id, collection_status='waiting to collect').exists()

"""
Renders the main page for patients, passes the user data and the presecription notification as context.
"""
def patients_dashboard_view(request):
    user_data = request.session.get('user_data')
    if not verify_user_role(user_data.get('role'), 'patient'):
        return redirect('/')

    prescription_notification = check_not_collected_prescriptions(user_data.get('patient_id'))

    context = {
        'user_data': user_data,
        'new_prescriptions_status': prescription_notification,
    }
    return render(request, 'patients_dashboard.html', context)