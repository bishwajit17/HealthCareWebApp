from django.shortcuts import render, redirect
from datetime import datetime
from django.http import JsonResponse
from database_models.models import PrescriptionsAssignments, PrescriptionCancellations, Staffs, Users
from collections import defaultdict
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
Displays prescription invoice
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
        row['issued_date'] = datetime.strftime(row['issued_date'], "%Y-%m-%d")

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

    return render(request, 'prescription_invoice.html', context)

"""
Displays prescription cancellation reason
"""
def prescription_cancellation_desc_view(request):
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

    return render(request, 'prescription_cancelled_desc.html', context)

"""
Logic for handling new prescription request
"""
def handle_prescription_request(request):
    if request.method == 'POST':
        user_data = request.session.get('user_data', {})
        prescription_payment_status = 1
        sel_prescription_id = request.POST.get('prescription_id')

        prescription_to_copy = PrescriptionsAssignments.objects.filter(
            appointment__patient=user_data.get('patient_id'),
            prescription = sel_prescription_id
        ).values(
            'prescription_assignment_id',
            'prescription_id',
            'appointment_id',
        )
        
        last_prescription_to_copy = prescription_to_copy.last()

        if user_data['payment_source'] == 'nhs':
            prescription_payment_status = 2

        new_prescription_data = PrescriptionsAssignments.objects.create(
            prescription_id=int(sel_prescription_id),
            appointment_id=last_prescription_to_copy['appointment_id'],
            prescription_cost=-1,
            prescription_status='requested',
            issued_date=None,
            collection_status='awaiting decision',
            quantity=0,
            prescription_payment_status=prescription_payment_status,
        )

        response_data = {'success': True, 'message': 'Prescription request handled successfully'}
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

"""
fetches all prescriptions assigned to patient by prescription name and type (sorted to ascending order)
"""
def fetch_prescription_list(patient_id):
    prescriptions = PrescriptionsAssignments.objects.filter(
        appointment__patient=patient_id
    ).values(
        'prescription_assignment_id',
        'prescription__prescription_id',
        'appointment_id',
        'prescription__prescription_name',
        'prescription__prescription_type',
        'quantity',
        'prescription_cost',
        'prescription_status',
        'issued_date',
        'collection_status',
        'prescription_payment_status'
    )

    prescriptions_dict = {}
    for prescription in prescriptions:
        prescription_assignment_id = prescription['prescription_assignment_id']
        prescription_id = prescription['prescription__prescription_id']
        prescription_name = prescription['prescription__prescription_name']
        prescription_type = prescription['prescription__prescription_type']
        issued_date = prescription['issued_date']

        if issued_date:
            issued_date = datetime.strftime(issued_date, "%Y-%m-%d")
        else:
            issued_date = '–'

        if prescription['quantity'] == 0:
            prescription['quantity'] = '–'

        prescription_info = {
            'prescription_assignment_id': prescription['prescription_assignment_id'],
            'quantity': prescription['quantity'],
            'prescription_status': prescription['prescription_status'],
            'issued_date': issued_date,
            'collection_status': prescription['collection_status'],
            'prescription_payment_status': get_payment_status(prescription['prescription_payment_status'])
        }

        if prescription_id in prescriptions_dict:
            prescriptions_dict[prescription_id]['info'].append(prescription_info)
        else:
            prescriptions_dict[prescription_id] = {
                'prescription_assignment_id': prescription_assignment_id,
                'prescription_name': prescription_name,
                'prescription_type': prescription_type,
                'info': [prescription_info]
            }

    prescriptions_dict = [
        {
            'prescription_id': prescription_id,
            'prescription_name': info['prescription_name'],
            'prescription_type': info['prescription_type'],
            'info': info['info']
        }
        for prescription_id, info in prescriptions_dict.items()
    ]

    prescriptions_dict.sort(key=lambda x: x['prescription_name'])

    return prescriptions_dict

"""
fetches the latest prescriptions or prescription requests sorted by appointment and doctor/nurse
"""
def fetch_appointment_prescription_list(patient_id):
    appointment_prescriptions = PrescriptionsAssignments.objects.filter(
        appointment__patient=patient_id
    ).select_related(
        'appointment__doctor_nurse', 
        'prescription'
    ).values(
        'appointment__appointment_id',
        'appointment__staff__user__name',
        'appointment__appointment_date',
        'appointment__appointment_start',
        'appointment__appointment_status',
        'appointment__appointment_outcome',
        'prescription__prescription_name',
        'prescription__prescription_type',
        'prescription_status',
        'prescription_assignment_id',
        'issued_date',
        'collection_status',
        'prescription_payment_status',
        'prescription_id',
    )

    # Group prescriptions by appointment details
    appointment_prescriptions_list = []
    appointments_by_details = defaultdict(list)
    for appt in appointment_prescriptions:
        key = (
            appt['appointment__appointment_id'],
            appt['appointment__staff__user__name'],
            appt['appointment__appointment_date'].strftime('%Y-%m-%d'),
            appt['appointment__appointment_start'].strftime('%H:%M'),
            appt['appointment__appointment_status'],
            appt['appointment__appointment_outcome']
        )
        appointments_by_details[key].append(appt)

    # Construct final appointments list
    for key, appt_prescriptions in appointments_by_details.items():
        appointment_data = {
            'appointment_id': key[0],
            'appointment_date': key[2],
            'appointment_time': key[3],
            'appointment_status': key[4],
            'appointment_outcome': key[5],
            'appointment_doctor': key[1],
            'prescriptions_info': []
        }

        # Separate prescriptions by prescription_id
        prescriptions_by_id = defaultdict(list)
        for prescription in appt_prescriptions:
            prescription_info = {
                'prescription_assignment_id': prescription['prescription_assignment_id'],
                'prescription_name': prescription['prescription__prescription_name'],
                'prescription_type': prescription['prescription__prescription_type'],
                'prescription_status': prescription['prescription_status'],
                'prescription_issue_date': prescription['issued_date'].strftime('%Y-%m-%d') if prescription['issued_date'] else '–',
                'prescription_outcome': prescription['collection_status'],
                'prescription_payment': get_payment_status(prescription['prescription_payment_status']),
                'prescription_id': prescription['prescription_id']
            }
            prescriptions_by_id[prescription['prescription_id']].append(prescription_info)

        # Filter 'awaiting decision' and 'waiting to collect' prescriptions
        for prescriptions in prescriptions_by_id.values():
            for outcome in prescriptions:
                if outcome['prescription_outcome'] == 'awaiting decision' or outcome['prescription_outcome'] == 'waiting to collect':
                    appointment_data['prescriptions_info'].append(outcome)
        
        # Filter 'cancelled' prescriptions
        for prescriptions in prescriptions_by_id.values():
            latest_cancelled_prescription = None
            for outcome in prescriptions:
                if outcome['prescription_outcome'] == 'cancelled':
                    latest_cancelled_prescription = outcome
            if not any(p['prescription_outcome'] in ['awaiting decision', 'waiting to collect', 'collected'] for p in prescriptions) and latest_cancelled_prescription:
                appointment_data['prescriptions_info'].append(latest_cancelled_prescription)

        # Filter 'collected' prescriptions
        for prescriptions in prescriptions_by_id.values():
            latest_collected_prescription = None
            latest_issued_date = None
            for outcome in prescriptions:
                if outcome['prescription_outcome'] == 'collected':
                    issued_date = outcome['prescription_issue_date']
                    if latest_issued_date is None or issued_date > latest_issued_date:
                        latest_issued_date = issued_date
                        latest_collected_prescription = outcome
                        
            if not any(p['prescription_outcome'] in ['awaiting decision', 'waiting to collect'] for p in prescriptions) and latest_collected_prescription:
                appointment_data['prescriptions_info'].append(latest_collected_prescription)
            
        appointment_prescriptions_list.append(appointment_data)

    return appointment_prescriptions_list

"""
Displays the prescriptions by name and type and latest prescriptions/requests per appointment
"""
def patients_prescription_view(request):
    user_data = request.session.get('user_data')
    if not verify_user_role(user_data.get('role'), 'patient'):
        return redirect('/')
    
    patient_id = user_data['patient_id']
    prescriptions = fetch_prescription_list(patient_id)
    appointment_prescriptions = fetch_appointment_prescription_list(patient_id)
    
    context = {
        'prescriptions': prescriptions,
        'appointment_prescriptions': appointment_prescriptions,
        'user_data': user_data,
    }

    return render(request, 'patients_prescription.html', context)
