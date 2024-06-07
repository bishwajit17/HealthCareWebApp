from django.shortcuts import redirect, render
from database_models.models import *
from django.http import JsonResponse
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

def appointment_details(request):
    if not request.session.get('user_data'):
        return redirect('admin_main')
    
    user_data = request.session.get('user_data')
    staff_members = Staffs.objects.select_related('user').filter(user__role__in=['doctor', 'nurse'])
    if staff_members.exists():
        first_staff = staff_members.first()
        appointments = Appointments.objects.filter(staff=first_staff, 
                                                   appointment_status='upcoming',
                                                ).select_related('patient__user', 'staff__user'
                                                ).values(
                                                        'appointment_id',
                                                        'appointment_date',
                                                        'appointment_start',
                                                        'appointment_end',
                                                        'appointment_status',
                                                        'appointment_outcome',
                                                        'patient_id',
                                                        'staff__user__role',
                                                        'staff_id',
                                                        'patient__user__name',
                                                ).order_by('-appointment_date', '-appointment_start')
    else:
        first_staff = None
        appointments = []

    cancel_types = CancellationTypes.objects.all()[:3]
    cancel_type_list = [{'id': ct.cancellation_type_id, 'type': ct.cancellation_type} for ct in cancel_types]
    
    context = {
        'staffs': staff_members,
        'first_staff': first_staff,
        'appointments': appointments,
        'user_data': user_data,
        'cancel_types': cancel_type_list,
    }

    return render(request, 'admin_appointments.html', context)

def update_list(request):
    if not request.session.get('user_data'):
        return redirect('admin_main')
    
    staff_id = request.GET.get('id')
    status = request.GET.get('status')
    staff = Staffs.objects.get(staff_id=staff_id)
    appointments = Appointments.objects.filter(staff=staff_id, 
                                                appointment_status=status,
                                            ).select_related('patient__user', 'staff__user'
                                            ).values(
                                                    'appointment_id',
                                                    'appointment_date',
                                                    'appointment_start',
                                                    'appointment_end',
                                                    'appointment_status',
                                                    'appointment_outcome',
                                                    'patient_id',
                                                    'staff__user__role',
                                                    'staff_id',
                                                    'patient__user__name',
                                            ).order_by('-appointment_date', '-appointment_start')
    
    cancel_types = CancellationTypes.objects.all()[:3]
    cancel_type_list = [{'id': ct.cancellation_type_id, 'type': ct.cancellation_type} for ct in cancel_types]
    
    context = {
        'appointments': list(appointments),
        'staff_name': staff.user.name,
        'cancel_type': cancel_type_list,
    }

    return JsonResponse(context, safe=False)

def cancel_appointment(request):
    if request.method == 'POST':
        if not request.session.get('user_data'):
            return redirect('admin_main')
        
        appointment_id = int(request.POST.get('id'))
        reason_id = int(request.POST.get('reason'))

        try:
            appointment = Appointments.objects.get(appointment_id=appointment_id)
            cancel_reason = CancellationTypes.objects.get(cancellation_type_id=reason_id)

            AppointmentCancellations.objects.update_or_create(
                appointment=appointment,
                description=cancel_reason.cancellation_type + " (Cancelled by Admin)",
                cancellation_type_id=reason_id
            )

            appointment.appointment_status = 'cancelled'
            appointment.appointment_outcome = 'cancelled'
            appointment.save()
            return JsonResponse("Appointment cancelled successfully.", safe=False)
        except ObjectDoesNotExist:
            return JsonResponse("No appointment found with the given details.", safe=False)
        
def appointment_invoice(request):
    appointment_id = request.GET.get('id')

    if not request.session.get('user_data'):
        return redirect('admin_main')
    
    user_data = request.session.get('user_data')
    
    invoice_data = Appointments.objects.filter(appointment_id=appointment_id
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
                                            )

    for data in invoice_data:
        start_time = datetime.combine(datetime.min, data['appointment_start'])
        end_time = datetime.combine(datetime.min, data['appointment_end'])
        duration = end_time - start_time
        duration_minutes = int(duration.total_seconds() // 60)
        start_time = data['appointment_start'].strftime('%H:%M')
        end_time = data['appointment_end'].strftime('%H:%M')

        appointment_info = {
            "user_data": user_data,
            "id": data['appointment_id'],
            "name": data['patient__user__name'],
            "type": data['staff__user__role'],
            "staff_name": data['staff__user__name'],
            "date": data['appointment_date'],
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration_minutes,
            "status": data['appointment_status'],
            "billing": data['patient__payment_source'],
            "cost": data['consultation_cost'],
            "outcome": data['appointment_outcome'],
        }

    response = render(request, 'admin_invoice.html', appointment_info)

    return response

def appointment_reason(request):
    if not request.session.get('user_data'):
        return redirect('admin_main')

    appointment_id = request.GET.get('id')
    user_data = request.session.get('user_data')

    app_data = Appointments.objects.filter(appointment_id=appointment_id
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

    response = render(request, 'admin_cancel.html', appointment_info)

    return response