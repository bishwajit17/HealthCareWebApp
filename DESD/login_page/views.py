from django.shortcuts import render,redirect
from django.contrib import messages
from database_models.models import Patients, Staffs, Users, Appointments, LoginAttempts, PrescriptionsAssignments, AppointmentCancellations, PrescriptionCancellations
from passlib.hash import sha256_crypt
from django.utils import timezone
import hashlib
from datetime import datetime, timedelta
from django.db import transaction

"""
Gets user data after passing username and role.
"""
def get_user_data(username, role):
    user_data = {}
    user_obj = Users.objects.get(username=username)
    user_id = user_obj.user_id

    common_data = {
        'user_id': user_id,
        'name': user_obj.name,
        'role': user_obj.role,
        'username': username,
        'date_of_birth': user_obj.date_of_birth.strftime("%Y-%m-%d"),
        'address': user_obj.address,
        'postcode': user_obj.postcode,
        'phone_number': user_obj.phone_number,
        'email': user_obj.email,
    }

    if role == 'patient':
        try:
            patient_obj = Patients.objects.get(user_id=user_id)
            user_data = {
                **common_data,
                'patient_id': patient_obj.patient_id,
                'payment_source': patient_obj.payment_source
            }
        except Patients.DoesNotExist:
            print("Patient does not exist")

    elif role in ['doctor', 'nurse', 'admin']:
        try:
            staff_obj = Staffs.objects.get(user_id=user_id)
            user_data = {
                **common_data,
                'staff_id': staff_obj.staff_id,
            }
        except Staffs.DoesNotExist:
            print("Doctor or Nurse does not exist")

    return user_data

"""
Sets the apppointment_status and appointment_outcome to 'cancelled'.
"""
def handle_past_appointment():
    past_appointment_id_list = check_past_appointments()
    for appointment_id in past_appointment_id_list:
        appointment = Appointments.objects.get(appointment_id=appointment_id)
        appointment.appointment_status = 'cancelled'
        appointment.appointment_outcome = 'cancelled'
        appointment.appointment_payment_status = 0
        appointment.save()

"""
Fetches all the appointment ids in a list that are past the appointment date and time.
"""
def check_past_appointments():
    current_datetime = timezone.now() + timedelta(hours=1)
    past_appointments = Appointments.objects.filter(
        appointment_status='upcoming',
        appointment_date__lte = current_datetime.date(),
        appointment_end__lte = current_datetime.time()
    ).values_list('appointment_id', flat=True)

    return past_appointments

"""
Find and set any upcoming appointments status with deleted staff or patient to 'cancelled'
"""
def check_deleted_user_appointments():
    deleted_user_ids = Users.objects.filter(role='deleted_user').values_list('user_id', flat=True)
    deleted_patient_ids = Patients.objects.filter(user_id__in=deleted_user_ids).values_list('patient_id', flat=True)
    deleted_staff_ids = Staffs.objects.filter(user_id__in=deleted_user_ids).values_list('staff_id', flat=True)

    # Fetch upcoming appointments for deleted patients and staff
    upcoming_patient_appointments = Appointments.objects.filter(appointment_status='upcoming', patient_id__in=deleted_patient_ids)
    upcoming_staff_appointments = Appointments.objects.filter(appointment_status='upcoming', staff_id__in=deleted_staff_ids)

    # Create appointment cancellations and update statuses in a single transaction
    with transaction.atomic():
        # Create appointment cancellations for deleted patients
        AppointmentCancellations.objects.bulk_create([
            AppointmentCancellations(
                appointment=appointment,
                description="Cancelled due to deleted user",
                cancellation_type_id=10,
            ) for appointment in upcoming_patient_appointments
        ])

        # Update appointment statuses and outcomes for deleted patients
        upcoming_patient_appointments.update(
            appointment_status='cancelled',
            appointment_outcome='cancelled',
            appointment_payment_status=0
        )

        # Create appointment cancellations for deleted staff
        AppointmentCancellations.objects.bulk_create([
            AppointmentCancellations(
                appointment=appointment,
                description="Cancelled due to deleted user",
                cancellation_type_id=10,
            ) for appointment in upcoming_staff_appointments
        ])

        # Update appointment statuses and outcomes for deleted staff
        upcoming_staff_appointments.update(
            appointment_status='cancelled',
            appointment_outcome='cancelled',
            appointment_payment_status=0
        )

"""
Find and set any 'waiting to collect' or 'awaiting decision' prescription status with deleted patient to 'cancelled'
"""
def check_deleted_user_prescriptions():
    deleted_user_ids = Users.objects.filter(role='deleted_user').values_list('user_id', flat=True)
    deleted_patient_ids = Patients.objects.filter(user_id__in=deleted_user_ids).values_list('patient_id', flat=True)
    prescribed_appointment_ids = Appointments.objects.filter(
        patient_id__in=deleted_patient_ids,
        appointment_outcome='prescribed'
    ).values_list('appointment_id', flat=True)

    # Filter prescription assignments based on prescribed appointment IDs and collection status
    prescription_assignments_to_cancel = PrescriptionsAssignments.objects.filter(
        appointment_id__in=prescribed_appointment_ids,
        collection_status__in=['waiting to collect', 'awaiting decision']
    )

    prescription_cancellations_to_create = []

    for assignment in prescription_assignments_to_cancel:
        if assignment.collection_status in ['waiting to collect', 'awaiting decision']:
            # Update prescription assignment
            assignment.prescription_status = 'request denied'
            assignment.collection_status = 'cancelled'
            assignment.prescription_payment_status = 0
            assignment.prescription_cost = -1
            assignment.issued_date = None
            assignment.save()

            # Create PrescriptionCancellations
            cancellation = PrescriptionCancellations(
                prescription_assignment=assignment,
                cancellation_type_id=10,
                description="Cancelled due to deleted user",
                staff_id=14
            )
            prescription_cancellations_to_create.append(cancellation)

    # Bulk create PrescriptionCancellations
    if prescription_cancellations_to_create:
        PrescriptionCancellations.objects.bulk_create(prescription_cancellations_to_create)


"""
Checks the number of invalid login attempts with the same username
returns 0 if the number of invalid logins with the same username is more than 5 and locks the account for 5 minutes.
returns 1 if the number of invalid logins with the same username is less than 5 and the current time is past the 5 minute lock.
"""
def check_invalid_login_attempts(username):
    login_attempts = LoginAttempts.objects.filter(username=username).count()

    if login_attempts:
        latest_login_attempt = LoginAttempts.objects.filter(username=username).latest('datetime')

        time_elapsed = timezone.now() - latest_login_attempt.datetime
        duration = timedelta(minutes=5)

        if login_attempts >=5 and time_elapsed < duration :
            return 0
        
    return 1

"""
Records invalid login attempts using the username and the datetime of the login.
"""
def record_login_attempt(username):
    LoginAttempts.objects.create(
        username=username,
        datetime=timezone.now()
    )

"""
This function is used for hashing password.
"""
def hash_password(password):
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    # hashed_pwd = sha256_crypt.hash((str(password)))
    return hashed_password

"""
Render SignupPage
"""
def signup_page(request):
    response = render(request,'signupPage.html')
    return response

"""
Render Login Page
"""
def login_page(request):
    request.session.flush()
    signup_confirm = request.GET.get('confirmation')
    session_expired = request.GET.get('session_expired')
    context = {
        'signup_confirm': signup_confirm == 'true',
        'session_expired': session_expired == 'true'
    }
    return render(request, 'login_page/loginPage.html', context)

"""
Handles user login validation, and redirects user to the appropiate dashboard screen (using user role) once validated.
"""
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        password = hash_password(password)
        request.session.flush()

        try:
            user = Users.objects.get(username=username, password=password)
            if check_invalid_login_attempts(username) == 1:
                LoginAttempts.objects.filter(username=username).delete()
                role = user.role
                user_data = get_user_data(user.username, role)
                request.session['user_data'] = user_data
                # handle_past_appointment()
                check_deleted_user_appointments()
                check_deleted_user_prescriptions()

                if role == 'patient':
                    return redirect('patient_main')
                elif role == 'admin':
                    return redirect('admin_main')
                else:
                    return redirect('doctor_nurse_main')
            else:
                messages.error(request, 'Account Locked. Try again later.')
        except Users.DoesNotExist:
            record_login_attempt(username)
            warning_count = 5 - LoginAttempts.objects.filter(username=username).count()

            if warning_count < 0:
                warning_count = 0
                messages.error(request, 'Account Locked. Try again later.')
            else:
                error_message = f'Username or password is incorrect. {warning_count} attempt(s) left.'
                messages.error(request, error_message)


    return redirect('/')