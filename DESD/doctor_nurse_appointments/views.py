from datetime import datetime, timedelta
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
import json
from django.shortcuts import redirect, render
from django.urls import reverse
from database_models.models import *
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from fuzzywuzzy import fuzz

def update_list(request): #backend calculation code 
    if request.method == 'GET':
        outcome = request.GET.get('outcome')
        if not request.session.get('user_data'):
            return redirect('doctor_nurse_main')
        user_data = request.session.get('user_data')
        staff_id = user_data.get('staff_id')
        cancel_types = CancellationTypes.objects.all()[:3]
        cancel_type_list = [{'id': ct.cancellation_type_id, 'type': ct.cancellation_type} for ct in cancel_types]

        appointments_data = Appointments.objects.filter(staff_id=staff_id,
                                                        appointment_outcome=outcome
                                                ).select_related('patient__user' 
                                                ).values(
                                                    'appointment_id',
                                                    'appointment_date',
                                                    'appointment_start',
                                                    'appointment_end',
                                                    'appointment_status',
                                                    'appointment_outcome',
                                                    'patient_id',
                                                    'patient__user__name',
                                                ).order_by('appointment_date', 'appointment_start')
        
        context = {
            'appointment': list(appointments_data),
            'cancel_type': cancel_type_list,
        }
    
    return JsonResponse(context, safe=False)


def appointments_list(request):
    if not request.session.get('user_data'):
        return redirect('doctor_nurse_main')
    
    if request.method == 'GET' and 'outcome' in request.GET:
        return update_list(request)

    user_data = request.session.get('user_data')
    staff_id = user_data.get('staff_id')
    
    appointments = Appointments.objects.filter(staff_id=staff_id,
                                               appointment_status='upcoming',
                                            ).select_related('patient__user'
                                            ).values(
                                                'appointment_id',
                                                'appointment_date',
                                                'appointment_start',
                                                'appointment_end',
                                                'appointment_status',
                                                'appointment_outcome',
                                                'patient_id',
                                                'patient__user__name',
                                            ).order_by('-appointment_date', '-appointment_start')

    cancel_types = CancellationTypes.objects.all()[:3]
    cancel_type_list = [{'id': ct.cancellation_type_id, 'type': ct.cancellation_type} for ct in cancel_types]
    
    context = {
        'appointments': appointments,
        'cancel_types': cancel_type_list,
        'user_data': user_data,
    }

    response = render(request,'doctor_nurse_appointments.html', context)

    return response 


def amend_booking_handling(request):
    user_data = request.session.get('user_data')
    staff_id = user_data.get('staff_id')
    role = user_data.get('role')

    if request.method == 'POST':
        selected_date = request.POST.get('date')
        selected_start = request.POST.get('start')
        selected_end = request.POST.get('end')
        selected_patient = request.POST.get('patient')
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
    else:
        selected_date_str = request.GET.get('date')
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")

    selected_day = selected_date.weekday() + 1

    try:
        schedule = Schedules.objects.get(day_id=selected_day, role=role)
    except Schedules.DoesNotExist:
        return JsonResponse({'error': "No Schedule found for the selected day."}, status=404)
    
    slots = Slots.objects.filter(schedule=schedule).order_by('start_time')
    appointments = Appointments.objects.filter(
                                            staff_id=staff_id,
                                            appointment_date=selected_date
                                            )
    
    slots_info = []
    duration_minutes_mapping = {1: 10, 2: 20, 3: 30}

    for slot in slots:
        duration_in_minutes = duration_minutes_mapping.get(slot.duration.duration_length)
        slot_end_time = (datetime.combine(selected_date, slot.start_time) + timedelta(minutes=duration_in_minutes)).time()

        overlapping_appointments = appointments.filter(
            Q(appointment_start__lt=slot_end_time),
            Q(appointment_end__gt=slot.start_time)
        ).exists()

        slots_info.append({
            'start_time': slot.start_time.strftime("%H:%M"),
            'end_time': slot_end_time.strftime("%H:%M"),
            'is_available': not overlapping_appointments
        })

    if request.method == 'POST':
        prev_appointment = Appointments.objects.select_related('patient__user').get(
                                                                patient_id=selected_patient,
                                                                appointment_date=selected_date,
                                                                appointment_start=selected_start,
                                                                appointment_end=selected_end,
                                                                staff_id=staff_id
                                                            )
    
        prev_appointment_dict = {
            'appointment_id': prev_appointment.appointment_id,
            'appointment_date': prev_appointment.appointment_date,
            'appointment_start': prev_appointment.appointment_start,
            'appointment_end': prev_appointment.appointment_end,
            'staff_id': prev_appointment.staff_id,
            'patient_id': prev_appointment.patient_id,
            'patient_name': prev_appointment.patient.user.name,
        }

        request.session['amendSlot'] = {
            'slots_info': json.dumps(slots_info, cls=DjangoJSONEncoder),
            'appointment': json.dumps(prev_appointment_dict, cls=DjangoJSONEncoder),
        }
        redirect_url = reverse('doctor_nurse_appointments:amend_booking')
        return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
    else: 
        return JsonResponse({'slots': slots_info})

def amend_booking(request):
    if not request.session.get('user_data'):
        return redirect('doctor_nurse_main')
    
    user_data = request.session.get('user_data')
    info = request.session.get('amendSlot')

    slots_info = json.loads(info.get('slots_info'))
    appointment = json.loads(info.get('appointment'))

    context = {
        'slots': slots_info,
        'appointment': appointment,
        'user_data': user_data,
    }

    return render(request, 'doctor_nurse_amendment.html', context)
    
def cancel_appointment(request):
    if request.method == 'POST':
        if not request.session.get('user_data'):
            return redirect('doctor_nurse_main')
        
        appointment_id = int(request.POST.get('id'))
        reason_id = int(request.POST.get('reason'))

        try:
            appointment = Appointments.objects.get(appointment_id=appointment_id)
            cancel_reason = CancellationTypes.objects.get(cancellation_type_id=reason_id)

            AppointmentCancellations.objects.update_or_create(
                appointment=appointment,
                description= cancel_reason.cancellation_type,
                cancellation_type_id=reason_id
            )

            appointment.appointment_status = 'cancelled'
            appointment.appointment_outcome = 'cancelled'
            appointment.save()
            return JsonResponse("Appointment cancelled successfully.", safe=False)
        except ObjectDoesNotExist:
            return JsonResponse("No appointment found with the given details.", safe=False)
        
def amend_confirmation_handling(request):
    if request.method == 'POST':
        if not request.session.get('user_data'):
            return redirect('doctor_nurse_main')
        appointment_id = request.POST.get('id')
        selected_date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()

        try:
            appointment = Appointments.objects.get(appointment_id=appointment_id)
            appointment.appointment_date = date
            appointment.appointment_start = start_time
            appointment.appointment_end = end_time
            appointment.save()

            return JsonResponse({"status": "success", "message": "Appointment updated successfully."})
        except Appointments.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Appointment not found."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": "An error occurred while updating the appointment."}, status=500)
        

def cancel_reason(request):
    if not request.session.get('user_data'):
        return redirect('doctor_nurse_main')

    appointment_id = request.GET.get('id')
    user_data = request.session.get('user_data')

    app_data = Appointments.objects.filter(
                                                appointment_id=appointment_id
                                            ).select_related('patient__user', 'staff__user'  
                                            ).values(
                                                'patient__user__name',
                                                'patient__payment_source',
                                                'staff__user__role',
                                                'staff__user__name',
                                                'appointment_id',
                                                'appointment_date',
                                                'appointment_start',
                                                'appointment_end',
                                                'appointment_status',
                                                'appointment_outcome',
                                                'consultation_cost'
                                            ).first()
    
    cancel_info = AppointmentCancellations.objects.filter(appointment_id=appointment_id).first()

    if app_data:
        start_time = datetime.combine(datetime.min, app_data['appointment_start'])
        end_time = datetime.combine(datetime.min, app_data['appointment_end'])
        duration = end_time - start_time
        duration_minutes = int(duration.total_seconds() // 60)
        start_time_formatted = app_data['appointment_start'].strftime('%H:%M')
        end_time_formatted = app_data['appointment_end'].strftime('%H:%M')

        appointment_info = {
            "user_data": user_data,
            "id": app_data['appointment_id'],
            "name": app_data['patient__user__name'],
            "type": app_data['staff__user__role'],
            "staff_name": app_data['staff__user__name'],
            "date": app_data['appointment_date'],
            "start_time": start_time_formatted,
            "end_time": end_time_formatted,
            "duration": duration_minutes,
            "status": app_data['appointment_status'],
            "billing": app_data['patient__payment_source'],
            "cost": app_data['consultation_cost'],
            "cancel_description": cancel_info.description if cancel_info else "No cancellation description"
        }

    response = render(request, 'doctor_nurse_cancel.html', appointment_info)

    return response

def forward_detail(request):
    if not request.session.get('user_data'):
        return redirect('doctor_nurse_main')

    appointment_id = request.GET.get('id')
    user_data = request.session.get('user_data')

    app_data = Appointments.objects.filter( appointment_id=appointment_id
                                            ).select_related('patient__user', 'staff__user'  
                                            ).values(
                                                'patient__user__name',
                                                'patient__payment_source',
                                                'staff__user__role',
                                                'staff__user__name',
                                                'appointment_id',
                                                'appointment_date',
                                                'appointment_start',
                                                'appointment_end',
                                                'appointment_status',
                                                'appointment_outcome',
                                                'consultation_cost'
                                            ).first()

    if app_data:
        start_time = datetime.combine(datetime.min, app_data['appointment_start'])
        end_time = datetime.combine(datetime.min, app_data['appointment_end'])
        duration = end_time - start_time
        duration_minutes = int(duration.total_seconds() // 60)
        start_time_formatted = app_data['appointment_start'].strftime('%H:%M')
        end_time_formatted = app_data['appointment_end'].strftime('%H:%M')

        appointment_info = {
            "user_data": user_data,
            "id": app_data['appointment_id'],
            "name": app_data['patient__user__name'],
            "type": app_data['staff__user__role'],
            "staff_name": app_data['staff__user__name'],
            "outcome": app_data['appointment_outcome'],
            "date": app_data['appointment_date'],
            "start_time": start_time_formatted,
            "end_time": end_time_formatted,
            "duration": duration_minutes,
            "status": app_data['appointment_status'],
            "billing": app_data['patient__payment_source'],
            "cost": app_data['consultation_cost'],
        }

    response = render(request, 'doctor_nurse_forward.html', appointment_info)

    return response

def prescribe_appointment(request):
    if not request.session.get('user_data'):
        return redirect('admin_main')
    
    appointment_id = request.POST.get('appointmentId')
    prescription_name = request.POST.get('prescription_name')
    prescription_type = request.POST.get('prescription_type')
    quantity = request.POST.get('quantity')
    cost = request.POST.get('cost')

    appointment = Appointments.objects.get(appointment_id=appointment_id)

    appointment.appointment_status = 'completed'
    appointment.appointment_outcome = 'prescribed'
    appointment.save()

    existing_prescriptions = Prescriptions.objects.all()
    similar_prescription_names = []

    for existing_prescription in existing_prescriptions:
        similarity_score = fuzz.ratio(existing_prescription.prescription_name, prescription_name)
        if similarity_score >= 85:
            similar_prescription_names.append(existing_prescription.prescription_name)

    if similar_prescription_names:
        similar_prescription = Prescriptions.objects.filter(prescription_name__in=similar_prescription_names, prescription_type=prescription_type).first()
        if similar_prescription:
            prescription_id = similar_prescription.prescription_id
        else:
            prescription_id = Prescriptions.objects.create(prescription_name=prescription_name, prescription_type=prescription_type)
    else:
        prescription_id = Prescriptions.objects.create(prescription_name=prescription_name, prescription_type=prescription_type)

    
    PrescriptionsAssignments.objects.create(prescription_cost=cost, 
                                            prescription_status='approved',
                                            issued_date=datetime.today().date(),
                                            quantity=quantity,
                                            collection_status='waiting to collect',
                                            prescription_payment_status=0,
                                            appointment_id=appointment_id,
                                            prescription_id=prescription_id)
    
    return JsonResponse({'success':True, 'message': 'Prescription submitted.'})

def forward_appointment(request):
    if not request.session.get('user_data'):
        return redirect('admin_main')
    
    appointment_id = request.POST.get('id')

    appointment = Appointments.objects.get(appointment_id=appointment_id)

    appointment.appointment_status = 'completed'
    appointment.appointment_outcome = 'forwarded'
    appointment.save()

    return JsonResponse({'success':True, 'message': 'Prescription submitted.'})