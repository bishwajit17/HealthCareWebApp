from django.shortcuts import render
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect
from database_models.models import Patients, Prescriptions, PrescriptionsAssignments, PrescriptionCancellations, Staffs, Users
from fuzzywuzzy import fuzz
from DESD.views import verify_user_role

"""
Reclassifies payment status
"""
def get_payment_status(status):
    if status == 0:
        return "Not Paid"
    elif status == 1:
        return "Paid"
    elif status == 2:
        return "Paid by NHS"
    else:
        return "Unknown"

"""
If date exists then change date format to yyyy-mm-dd else return '–'
"""
def set_date_format(date):
    if date is None:
        return '–'
    else:
        return datetime.strftime(date, "%Y-%m-%d")

"""
Function to mark selected prescription request as 'request denied' and collection_status as 'cancelled' in the database.
"""
def handle_prescription_cancellation(request):
    if request.method == 'POST':
        user_data = request.session.get('user_data', {})
        sel_prescription_assignment_id = request.POST.get('prescription_assignment_id')
        sel_cancellation_type_id = request.POST.get('cancellationType')
        sel_description = request.POST.get('cancelReason')
        
        # Update Prescription Assignment
        update_prescription_assignments = PrescriptionsAssignments.objects.filter(
            prescription_assignment_id = sel_prescription_assignment_id
        ).update(
            prescription_status="request denied",
            issued_date=None,
            collection_status="cancelled",
            prescription_cost=-1,
            quantity=0,
            prescription_payment_status=0,
        )
        # Add new Cancellation Record
        prescription_cancellation_data = PrescriptionCancellations.objects.create(
            description=sel_description,
            cancellation_type_id=sel_cancellation_type_id,
            prescription_assignment_id=sel_prescription_assignment_id,
            staff_id=user_data['staff_id']
        )

        return redirect('doctor_nurse_prescriptions')

"""
Function to mark selected prescription request as 'approved' and to make changes to the prescription data in the database.
"""
def handle_prescription_approval(request):
    if request.method == 'POST':
        sel_patient_id = request.POST.get('patient_id')
        sel_prescription_assignment_id = request.POST.get('prescription_assignment_id')
        sel_prescription_name = request.POST.get('prescription_name')
        sel_prescription_type = request.POST.get('prescription_type')
        sel_quantity = request.POST.get('quantity')
        sel_cost = request.POST.get('cost')

        patient_data = Patients.objects.get(patient_id=sel_patient_id)
        payment_source = patient_data.payment_source

        sel_prescription_payment_status = 0
        if payment_source == 'nhs':
            sel_prescription_payment_status = 2
        
        existing_prescriptions = Prescriptions.objects.all()
        similar_prescription_names = []

        # Iterate through existing prescriptions
        for existing_prescription in existing_prescriptions:
            similarity_score = fuzz.ratio(existing_prescription.prescription_name, sel_prescription_name)
            if similarity_score >= 85:
                similar_prescription_names.append(existing_prescription.prescription_name)

        if similar_prescription_names:
            # Similar pres name exists
            similar_prescription = Prescriptions.objects.filter(prescription_name__in=similar_prescription_names, prescription_type=sel_prescription_type).first()
            if similar_prescription:
                # Pres name and type match
                sel_prescription_name = similar_prescription.prescription_name
            else:
                # Type different, create new pres
                new_prescription = Prescriptions.objects.create(prescription_name=sel_prescription_name, prescription_type=sel_prescription_type)
                PrescriptionsAssignments.objects.filter(prescription_assignment_id=sel_prescription_assignment_id).update(prescription_id=new_prescription.prescription_id)
        else:
            # Name different, create new pres
            new_prescription = Prescriptions.objects.create(prescription_name=sel_prescription_name, prescription_type=sel_prescription_type)
            PrescriptionsAssignments.objects.filter(prescription_assignment_id=sel_prescription_assignment_id).update(prescription_id=new_prescription.prescription_id)

        # Approve Prescription Assignment
        update_prescription_assignments = PrescriptionsAssignments.objects.filter(
            prescription_assignment_id = sel_prescription_assignment_id
        ).update(
            prescription_status="approved",
            issued_date=datetime.today().strftime('%Y-%m-%d'),
            collection_status="waiting to collect",
            quantity=sel_quantity,
            prescription_cost=sel_cost,
            prescription_payment_status=sel_prescription_payment_status
        )

        return redirect('doctor_nurse_prescriptions')

"""
Function to check if the person's billing type is NHS or private by using prescription assignment id
"""
def check_billing_type(sel_prescription_assignment_id):
    prescription_assignment = PrescriptionsAssignments.objects.get(prescription_assignment_id=sel_prescription_assignment_id)
    
    # Get the appointment associated with the prescription assignment
    appointment = prescription_assignment.appointment
    
    # Get the patient associated with the appointment
    patient = appointment.patient
    
    # Check the payment source of the patient
    payment_source = patient.payment_source
    
    if payment_source == 'nhs':
        return 2
    elif payment_source == 'private':
        return 1
    else:
        return 0

"""
Function to set collection_status to 'collected' in the database.
"""
def handle_mark_collected(request):
    if request.method == 'POST':
        sel_prescription_assignment_id = request.POST.get('prescription_assignment_id')
        sel_prescription_payment_status = check_billing_type(sel_prescription_assignment_id)

        update_prescription_assignments = PrescriptionsAssignments.objects.filter(
            prescription_assignment_id=sel_prescription_assignment_id).update(
                collection_status="collected",
                prescription_payment_status=sel_prescription_payment_status
            )

        response_data = {'status': 'success'}
        response = JsonResponse(response_data)
        response.set_cookie('prescription_updated', 'true')
        
        return response

"""
Function to view cancellation prescription request reason/invoice.
"""
def prescription_cancellation_reason_view(request):
    sel_prescription_assignment_id = request.GET.get('prescription_assignment_id')
    user_data = request.session.get('user_data', {})

    prescription_cancellations = PrescriptionCancellations.objects.filter(
        prescription_assignment_id=sel_prescription_assignment_id
    ).select_related(
        'cancellation_type'
    ).values(
        'prescription_assignment__appointment__patient__user__name',
        'prescription_assignment__prescription__prescription_name',
        'prescription_assignment__prescription__prescription_type',
        'prescription_cancellation_id',
        'cancellation_type__cancellation_type',
        'staff_id',
        'description',
    )

    cancellation_reason_list = []

    for row in prescription_cancellations:
        staff_id = row['staff_id']
        staff = Staffs.objects.get(staff_id=staff_id)
        user_id = staff.user_id

        user = Users.objects.get(user_id=user_id)
        user_name = user.name

        cancellation_reason_dict = {
            'prescription_cancellation_id': row['prescription_cancellation_id'],
            'patient_name': row['prescription_assignment__appointment__patient__user__name'],
            'prescription_name': row['prescription_assignment__prescription__prescription_name'],
            'prescription_type': row['prescription_assignment__prescription__prescription_type'],
            'cancellation_type': row['cancellation_type__cancellation_type'],
            'staff_name': user_name,
            'description': row['description'],
        }

        cancellation_reason_list.append(cancellation_reason_dict)

    context = {
        'prescription_cancellations': cancellation_reason_list,
        'user_data': user_data,
    }

    return render(request, 'view_cancellation_reason.html', context)

"""
Function to view prescription invoice.
"""
def prescription_invoice_view(request):
    sel_prescription_assignment_id = request.GET.get('prescription_assignment_id')
    user_data = request.session.get('user_data', {})

    prescription_invoice = PrescriptionsAssignments.objects.filter(
        prescription_assignment_id=sel_prescription_assignment_id
    ).values(
        'prescription_assignment_id',
        'appointment__patient__user__name',
        'prescription__prescription_name',
        'prescription__prescription_type',
        'issued_date',
        'quantity',
        'prescription_cost',
        'collection_status',
        'prescription_payment_status',
        'appointment__patient__payment_source',
        'appointment__staff__user__name',
    )

    prescription_invoice_list = []

    for row in prescription_invoice:
        row['prescription_payment_status'] = get_payment_status(row['prescription_payment_status'])
        row['issued_date'] = set_date_format(row['issued_date'])

        prescription_invoice = {
            'prescription_assignment_id': row['prescription_assignment_id'],
            'patient_name': row['appointment__patient__user__name'],
            'prescription_name': row['prescription__prescription_name'],
            'prescription_type': row['prescription__prescription_type'],
            'issued_date': row['issued_date'],
            'quantity': row['quantity'],
            'prescription_cost': row['prescription_cost'],
            'collection_status': row['collection_status'],
            'prescription_payment_status': row['prescription_payment_status'],
            'payment_source': row['appointment__patient__payment_source'],
            'staff_name': row['appointment__staff__user__name'],
        }

        prescription_invoice_list.append(prescription_invoice)

    context = {
        'prescription_invoice': prescription_invoice_list,
        'user_data': user_data,
    }

    return render(request, 'view_prescription_invoice.html', context)

"""
Function to get all prescription assignments which have collection_status='collected' or 'cancelled'.
The function returns a list of dictionaries and contains the following contents:
'prescription_assignment_id',
'patient_name',
'prescription_name',
'prescription_type',
'prescription_status',
'collection_status,
'issued_date'
"""
def get_collected_and_cancelled_prescription_list(request):
    if request.method == 'POST':
        collection_statuses = ['collected', 'cancelled']

        collected_and_cancelled_prescriptions = PrescriptionsAssignments.objects.filter(
            collection_status__in=collection_statuses
        ).values(
            'prescription_assignment_id',
            'appointment__patient__user__name',
            'prescription__prescription_name',
            'prescription__prescription_type',
            'prescription_status',
            'collection_status',
            'issued_date',
        )

        collected_and_cancelled_list = []
        for row in collected_and_cancelled_prescriptions:
            row['issued_date'] = set_date_format(row['issued_date'])

            collected_and_cancelled_dict = {
                'prescription_assignment_id': row['prescription_assignment_id'],
                'patient_name': row['appointment__patient__user__name'],
                'prescription_name': row['prescription__prescription_name'],
                'prescription_type': row['prescription__prescription_type'],
                'prescription_status': row['prescription_status'],
                'collection_status': row['collection_status'],
                'issued_date': row['issued_date']
            }
            collected_and_cancelled_list.append(collected_and_cancelled_dict)
        collected_and_cancelled_list = sorted(collected_and_cancelled_list, key=lambda x: x['issued_date'], reverse=True)

        return JsonResponse({'collected_and_cancelled_list': collected_and_cancelled_list})

"""
Function to get all prescription assignments which have collection_status='awaiting decision'.
The function returns a list of dictionaries and contains the following contents:
'prescription_id',
'prescription_assignment_id',
'patient_name',
'prescription_name',
'prescription_type',
'prescription_status',
'collection_status,
"""
def get_awaiting_decision_prescription_list(request):
    if request.method == 'POST':
        awaiting_decision_prescriptions = PrescriptionsAssignments.objects.filter(
            collection_status='awaiting decision'
        ).values(
            'prescription_id',
            'prescription_assignment_id',
            'appointment__patient_id',
            'appointment__patient__user__name',
            'prescription__prescription_name',
            'prescription__prescription_type',
            'prescription_status',
            'collection_status',
        )

        awaiting_decision_list = []
        for row in awaiting_decision_prescriptions:
            awaiting_decision_dict = {
                'prescription_id': row['prescription_id'],
                'prescription_assignment_id': row['prescription_assignment_id'],
                'patient_id': row['appointment__patient_id'],
                'patient_name': row['appointment__patient__user__name'],
                'prescription_name': row['prescription__prescription_name'],
                'prescription_type': row['prescription__prescription_type'],
                'prescription_status': row['prescription_status'],
                'collection_status': row['collection_status'],
            }
            awaiting_decision_list.append(awaiting_decision_dict)
        return JsonResponse({'awaiting_decision_list': awaiting_decision_list})

"""
Function to get all prescription assignments which have collection_status='waiting to collect'.
The function returns a list of dictionaries and contains the following contents:
'prescription_assignment_id',
'patient_name',
'prescription_name',
'prescription_type',
'prescription_status',
'collection_status,
'issued_date'
"""
def get_waiting_to_collect_prescription_list(request):
    if request.method == 'POST':
        waiting_to_collect_prescriptions = PrescriptionsAssignments.objects.filter(
            collection_status='waiting to collect'
        ).values(
            'prescription_assignment_id',
            'appointment__patient__user__name',
            'prescription__prescription_name',
            'prescription__prescription_type',
            'prescription_status',
            'collection_status',
            'issued_date',
        )

        waiting_to_collect_list = []
        for row in waiting_to_collect_prescriptions:
            row['issued_date'] = set_date_format(row['issued_date'])

            cwaiting_to_collect_dict = {
                'prescription_assignment_id': row['prescription_assignment_id'],
                'patient_name': row['appointment__patient__user__name'],
                'prescription_name': row['prescription__prescription_name'],
                'prescription_type': row['prescription__prescription_type'],
                'prescription_status': row['prescription_status'],
                'collection_status': row['collection_status'],
                'issued_date': row['issued_date']
            }
            waiting_to_collect_list.append(cwaiting_to_collect_dict)
        waiting_to_collect_list = sorted(waiting_to_collect_list, key=lambda x: x['issued_date'], reverse=True)

        return JsonResponse({'waiting_to_collect_list': waiting_to_collect_list})

"""
Fetches all 3 prescription list dictionaries (defined above) and displays them in the doctor/nurse prescription screen [#15]  
"""
def doctor_nurse_prescription_view(request):
    user_data = request.session.get('user_data')
    if not verify_user_role(user_data.get('role'), ['doctor', 'nurse']):
        return redirect('/')
    
    context = {
        'user_data': user_data,
    }

    return render(request, 'doctor_nurse_prescriptions.html', context)
