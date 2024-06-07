import os
import django
from multiprocessing import Pool, cpu_count, get_context
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DESD.settings')
django.setup()
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.utils.dateparse import parse_time
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.core import serializers
from database_models.models import *
from datetime import datetime, timedelta, date
import random
from .time_slots import time_slots
import json
from django.utils.timezone import make_aware

# def generate_calendar(start_date, end_date):

#     start_time = datetime.strptime("09:00", "%H:%M")
#     end_time = datetime.strptime("18:00", "%H:%M")
#     total_minutes = (end_time - start_time).seconds // 60  

#     calendar = []

#     current_date = start_date
#     while current_date <= end_date:
#         if (current_date.weekday() not in [5, 6]) or (end_date - start_date).days != 6:
#             day_calendar = {'day': current_date.strftime("%A"), 'slots': {}}
#             current_time = start_time
#             remaining_minutes = total_minutes

#             while remaining_minutes > 0:
#                 slot_duration = random.choice([10, 20, 30])
#                 slot_duration = min(slot_duration, remaining_minutes)
#                 slot_end_time = current_time + timedelta(minutes=slot_duration)
#                 day_calendar['slots'][current_time.strftime("%H:%M")] = slot_duration // 10
#                 current_time = slot_end_time
#                 remaining_minutes -= slot_duration

#             calendar.append(day_calendar)

#         current_date += timedelta(days=1)

#     return calendar

#05/03/2024 -- Yie Nian Chu -- New function added: calculate the first date of the week (Monday) with the given date -- LINE 40 -- <<Start>> --
def date_reset(): #backend calculation code
    today = date.today().weekday()

    match today:
        case 1:
            start_date = date.today() - timedelta(days=1)
        case 2:
            start_date = date.today() - timedelta(days=2)
        case 3:
            start_date = date.today() - timedelta(days=3)
        case 4:
            start_date = date.today() - timedelta(days=4)
        case 5:
            start_date = date.today() - timedelta(days=5)
        case 6:
            start_date = date.today() - timedelta(days=6)
        case _:
            start_date = date.today()

    end_date = start_date + timedelta(days=6)

    return start_date, end_date
#05/03/2024 -- Yie Nian Chu -- New function added: calculate the first date of the week (Monday) with the given date -- LINE 40 -- <<End>> --

#05/03/2024 -- Yie Nian Chu -- New function added: update calendar when user selected different staff roles or different date range -- LINE 65 -- <<Start>> --
def update_calendar(request): #backend calculation code 
    
    if request.method == 'GET':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if not request.session.get('user_data'):
            return redirect('patient_main')
        user_data = request.session.get('user_data')
        role = request.GET.get('role')

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if request.session.get('amendBooking'):
            slot_detail = request.session.get('amendBooking')
            calendar = fetch_calendar_data(start_date, end_date, user_data, role, slot_detail['start_time'], slot_detail['selected_date'])
        elif request.session.get('adminAmendment'):
            slot_detail = request.session.get('adminAmendment')
            calendar = fetch_calendar_data(start_date, end_date, slot_detail['patient_data'], role, slot_detail['start_time'], slot_detail['selected_date'])
        else:
            calendar = fetch_calendar_data(start_date, end_date, user_data, role)

        context = {
            'available_slot': calendar,
            'total_slots': time_slots
        }
    
    return JsonResponse(context)

#05/03/2024 -- Yie Nian Chu -- New function added: update calendar when user selected different staff roles or different date range -- LINE 65 -- <<End>> --

#05/03/2024 -- Yie Nian Chu -- New function added: fetch doctor/nurse working hours from database -- LINE 89 -- <<Start>> --
def staff_calendar(role): #backend verification code
    monday, tuesday, wednesday, thursday, friday = [], [], [] ,[] ,[]
    calendar = [monday, tuesday, wednesday, thursday, friday]
    staff_timetable = Staffs.objects.filter(user__role=role).select_related('user')
    staff_timetable = list(staff_timetable)

    #if staff is working full-time, then his/her staff_id will be in all days, if its part-time, then verify which day is he/her working on
    for staff in staff_timetable:
        if staff.hour_type == 'full':
            for day in calendar:
                day.append(staff.staff_id)
        elif staff.hour_type == 'part':
            if staff.monday == 1:
                monday.append(staff.staff_id)
            if staff.tuesday == 1:
                tuesday.append(staff.staff_id)
            if staff.wednesday == 1:
                wednesday.append(staff.staff_id)
            if staff.thursday == 1:
                thursday.append(staff.staff_id)
            if staff.friday == 1:
                friday.append(staff.staff_id)

    return calendar

def worker_init():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DESD.settings')
    import django
    django.setup()

def process_day_data(day_data):
    appointments, day_index, day, day_map, selected_role, start_time, role_schedules, current_datetime, date_obj, patient = day_data
    # print(f"Processing {day} on process ID: {os.getpid()}")
    day_mapping = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
    date = day_map[day]
    day_id = day_mapping[day]
    available_staff = role_schedules[day_index]
    schedules_for_selected_role = Schedules.objects.filter(day_id=day_id, role=selected_role)
    slot_dict = {}

    for schedule in schedules_for_selected_role:
        slots = Slots.objects.filter(schedule=schedule)

        for slot in slots:
            time_str = slot.start_time.strftime("%H:%M")
            overlapping_appointments = appointments.get(date, {}).get(time_str, [])
            duration = slot.duration.duration_length
            datetime_slot_start = datetime.combine(date, slot.start_time)
            datetime_slot_end = datetime_slot_start + timedelta(minutes=duration*10)
            state = 0
            selected_staff = random.choice(available_staff)
            appointment_validation = appointments.get(date, {})

            if len(overlapping_appointments) <= len(available_staff):
                for app in appointment_validation.items():
                        app_start = datetime.combine(date, app[1][0]['appointment'].appointment_start)
                        app_end = datetime.combine(date, app[1][0]['appointment'].appointment_end)

                        if app_end > datetime_slot_start and app_start < datetime_slot_end: 
                            if app[1][0]['patient'] == patient.patient_id:   
                                if app[1][0]['staff_id'] in available_staff:
                                    if app[1][0]['appointment'].appointment_status == 'cancelled':
                                        state = 3
                                    else:
                                        state = 2
                                else:
                                    state = 1                  
                                selected_staff = app[1][0]['staff_id']
                                break
                            else:
                                if app[1][0]['staff_id'] in available_staff:
                                    state = 1
                                else:
                                    state = 0                   
                                break
                    
            else:
                state = 1
                for app in appointment_validation.items():
                    if app[1][0]['appointment'].appointment_date == date and app[1][0]['appointment'].appointment_start.strftime('%H:%M'):
                        selected_staff = app[1][0]['staff_id']
                        break

            if date_obj is not None and start_time is not None:
                if date == date_obj and time_str == start_time:
                    state = 4

            is_today_or_future = date > current_datetime.date() or (date == current_datetime.date() and slot.start_time > current_datetime.time())
            if not is_today_or_future:
                state = 1

            slot_id = (datetime_slot_start.hour * 6) + (datetime_slot_start.minute // 10)
            url_params = f'?duration={slot.duration.duration_length}&time={time_str}&date={date.isoformat()}&staff_id={selected_staff}'
            url = reverse('booking:slot_selection_handling') + url_params

            slot_dict[time_str] = {
                'duration': duration,
                'slot_id': slot_id,
                'state': state,
                'staff_id': selected_staff,
                'url': url,
            }
    return {'day': day, 'slots': slot_dict}


def timetable_to_calendar(appointments, day_map, user_id, selected_role, start_time=None, selected_date=None):

    patient = Patients.objects.get(user_id=user_id)
    current_datetime = datetime.now()

    role_schedules = staff_calendar(selected_role)

    if selected_date and start_time:
        date_obj = datetime.strptime(selected_date.split(" GMT")[0], "%a %b %d %Y %H:%M:%S").date()
    else:
        date_obj = None

    timetable = []
    interested_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    day_data_list = [
        (appointments, day_index, day, day_map, selected_role, start_time, role_schedules, current_datetime, date_obj, patient)
        for day_index, day in enumerate(interested_days) if role_schedules[day_index]
    ]

    num_processes = cpu_count()
    ctx = get_context('spawn')
    with ctx.Pool(processes=num_processes, initializer=worker_init) as pool:
        timetable = pool.map(process_day_data, day_data_list)

    return timetable

def fetch_calendar_data(start_date, end_date, user_data, role, start_time=None, selected_date=None): #backend calculation code
    #used to map the date to each day
    DAY_MAPPING = {
    'Monday': start_date,
    'Tuesday': start_date + timedelta(days=1),
    'Wednesday': start_date + timedelta(days=2),
    'Thursday': start_date + timedelta(days=3),
    'Friday': start_date + timedelta(days=4),
    }

    appointments = Appointments.objects.filter(appointment_date__range=(start_date, end_date),
                                               appointment_start__range=(datetime.combine(start_date, datetime.min.time()), datetime.combine(end_date, datetime.max.time()))
                                               ).select_related('staff__user')

    appointments_data = {}
    appointments = list(appointments) #converting the fetched data into list for easier looping
    if len(appointments) > 0: #if there is appointments, store the appointment data into appointments_data (dict) for further validation
        for appointment in appointments:
            appointment_date = appointment.appointment_date
            appointment_time = appointment.appointment_start.strftime('%H:%M')
            patient_id = appointment.patient_id
            staff_id = appointment.staff_id
            staff_role = appointment.staff.user.role 
            appointments_data.setdefault(appointment_date, {}).setdefault(appointment_time, []).append({
            'appointment': appointment,
            'role': staff_role,
            'staff_id': staff_id,
            'patient': patient_id
            })

    timetable = timetable_to_calendar(appointments_data, DAY_MAPPING, user_data.get('user_id'), role, start_time, selected_date)

    return timetable

#-- This is the view page used to render "/bookings/" --#
def new_booking(request): #backend and frontend code
    #return to login if session expired
    if not request.session.get('user_data'):
        return redirect('patient_main')

    user_data = request.session.get('user_data')

    if request.method == 'POST':
        role = request.POST.get('role')
        start_date = request.POST.get('start_date')
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=7)
        selected_date = request.POST.get('selected_date')
        start_time = request.POST.get('start_time')
        patient_id = request.POST.get('patient_id')
        staff_id = request.POST.get('staff_id')
        
        if selected_date != None and start_time != None and role != None and start_date != None and patient_id == None and staff_id == None:
            slot_detail = {
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'role': role,
                'start_time': start_time,
                'selected_date': selected_date,
            }

            request.session['amendBooking'] = slot_detail

        elif role != None and start_date != None and patient_id == None and staff_id == None:
            slot_detail = {
                'start_date': start_date.strftime("%Y-%m-%d"),
                'role': role,
            }
            request.session['slot_info'] = slot_detail

        elif patient_id != None and staff_id != None:
            patient_data = Patients.objects.filter(patient_id=patient_id).values('patient_id', 'user_id', 'user__name').first()

            slot_detail = {
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'role': role,
                'start_time': start_time,
                'selected_date': selected_date,
                'patient_data': patient_data,
                'staff_id': staff_id,
            }
            request.session['adminAmendment'] = slot_detail

        context = {
            'user_data': user_data,
            'start_date': start_date,
            'end_date': end_date,
            'role': role,
        }
    else:
        context = {
            'user_data': user_data
        }


    response = render(request,'patients_appointments.html', context)
    return response

def fetch_calendar(request):  
    #return to login if session expired
    if not request.session.get('user_data'):
        return redirect('patient_main')
    
    user_data = request.session.get('user_data')

    if request.method == 'GET':
        return update_calendar(request)
    else:
        if request.session.get('slot_info'):
            selected_slot = request.session.get('slot_info', {})
            start_date = selected_slot.get('start_date')
            role = selected_slot.get('role')
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = start_date + timedelta(days=7)
            del request.session['slot_info']
            calendar = fetch_calendar_data(start_date, end_date, user_data, role)
        elif request.session.get('amendBooking'):
            slot_detail = request.session.get('amendBooking')
            start_date = datetime.strptime(slot_detail['start_date'], "%Y-%m-%d").date()
            end_date = datetime.strptime(slot_detail['end_date'], "%Y-%m-%d").date()
            role = slot_detail['role']
            calendar = fetch_calendar_data(start_date, end_date, user_data, role, slot_detail['start_time'], slot_detail['selected_date'])
        elif request.session.get('adminAmendment'):
            slot_detail = request.session.get('adminAmendment')
            start_date = datetime.strptime(slot_detail['start_date'], "%Y-%m-%d").date()
            end_date = datetime.strptime(slot_detail['end_date'], "%Y-%m-%d").date()
            role = slot_detail['role']
            calendar = fetch_calendar_data(start_date, end_date, slot_detail['patient_data'], slot_detail['role'], slot_detail['start_time'], slot_detail['selected_date'])

        else:
            role = 'doctor'
            start_date, end_date = date_reset()
            calendar = fetch_calendar_data(start_date, end_date, user_data, role)

        context = {
            'start_date': start_date,
            'end_date': end_date,
            'role': role,
            'available_slot': calendar,
            'total_slots': time_slots,
            'user_data': user_data,
        }

        return JsonResponse(context)



# -- This is the backend code for handling the user selected time slots with ajax. -- #
def slot_selection_handling(request): #backend handling code
    selected_type = request.POST.get('type')
    selected_date = request.POST.get('date')
    selected_time = request.POST.get('time')
    selected_duration = request.POST.get('duration')
    selected_staff = request.POST.get('staff_id')

    start_time = datetime.strptime(selected_time, "%H:%M").time()
    duration = timedelta(minutes=int(selected_duration))
    date_end = datetime.combine(datetime.strptime(selected_date, "%Y-%m-%d").date(), start_time) + duration
    end_time = date_end.time()

    start_time = start_time.strftime("%H:%M")
    end_time = end_time.strftime("%H:%M")

    request.session['selectedSlot'] = {
        'type': selected_type,
        'date': selected_date,
        'start_time': start_time,
        'end_time': end_time,
        'staff_id': selected_staff,
        'duration': selected_duration
    }

    redirect_url = reverse('patients_appointments:patient_slot_confirmation')

    return JsonResponse({'status': 'success', 'redirect_url': redirect_url})

# -- This is the view for rendering the slot confirmation page -- #
@never_cache
def patient_slot_confirmation(request): #frontend rendering code
    if not request.session.get('selectedSlot'):
        return redirect('patient_main')

    if not request.session.get('user_data'):
        return redirect('patient_main')
    user_data = request.session.get('user_data')

    selected_slot = request.session.get('selectedSlot', {})
    staff_rate = StaffRates.objects.filter(rate_type = selected_slot.get('type'))
    staff_details = Staffs.objects.select_related('user').get(staff_id=selected_slot.get('staff_id'))
    name = staff_details.user.name
    staff_timetable = staff_calendar(selected_slot.get('type'))
    weekday = datetime.strptime(selected_slot.get('date'), '%Y-%m-%d').weekday()

    match (weekday):
        case 0:
            index = 0
        case 1:
            index = 1
        case 2:
            index = 2
        case 3:
            index = 3
        case 4:
            index = 4
        case _:
            index = 0
    
    #get the available staff_id for that particular time slot but excluding the previous random allocated one  
    if int(selected_slot.get('staff_id')) in staff_timetable[index]:
        staff_timetable[index].remove(int(selected_slot.get('staff_id')))
    available_staff_id = staff_timetable[index]
    available_staff = {}


    for id in available_staff_id:
        staff = Staffs.objects.select_related('user').get(staff_id=id)
        available_staff[id] = staff.user.name

    for rate in staff_rate:
        rate_per_hr = rate.rate_per_hr

    #calculate the consultation cost
    rate_per_min = rate_per_hr / 60
    consultation_cost = round(rate_per_min * int(selected_slot.get('duration')), 2)

    context = {
        'available_staff': available_staff,
        'staff_name': name,
        'staff_id': selected_slot.get('staff_id'),
        'selected_type': selected_slot.get('type'),
        'selected_date': selected_slot.get('date'),
        'selected_start_time': selected_slot.get('start_time'),
        'selected_end_time': selected_slot.get('end_time'),
        'selected_duration': selected_slot.get('duration'),
        'consultation_cost': consultation_cost,
        'user_data': user_data,
    }

    response = render(request, 'selected_slot.html', context)

    return response

@never_cache
def slot_confirmation_handling(request): #backend handling code
    if not request.session.get('user_data'):
        return redirect('patient_main')
    
    user_data = request.session.get('user_data')
    
    if request.session.get('amendBooking') or request.session.get('adminAmendment'):
        if request.session.get('amendBooking'):
            previous_appointment = request.session.get('amendBooking')
        elif request.session.get('adminAmendment'):
            previous_appointment = request.session.get('adminAmendment')
        
        prev_appointment_date = datetime.strptime(previous_appointment['selected_date'].split(' GMT')[0], "%a %b %d %Y %H:%M:%S").strftime("%Y-%m-%d")

        if request.session.get('amendBooking'):
            appointment_to_delete = Appointments.objects.filter(appointment_date=prev_appointment_date, 
                                                    appointment_start=previous_appointment['start_time'],
                                                    patient_id=user_data.get('patient_id')) 
            if appointment_to_delete.exists():
                appointment_to_delete.delete()
                del request.session['amendBooking']
        elif request.session.get('adminAmendment'):
            appointment_to_delete = Appointments.objects.filter(appointment_date=prev_appointment_date, 
                                                                appointment_start=previous_appointment['start_time'],
                                                                patient_id=previous_appointment['patient_data'].get('patient_id'))
            if appointment_to_delete.exists():
                appointment_to_delete.delete()

    selected_slot = request.session.get('selectedSlot', {})
    consultation_cost = request.POST.get('cost')
    staff_id = request.POST.get('staff')

    selected_slot['staff_id'] = staff_id
    request.session['selectedSlot'] = selected_slot



    appointment_status = 'upcoming'
    appointment_outcome = 'awaiting'
    appointment_payment_status = 1 if user_data.get('payment_source') == 'nhs' else 0
    patient_id = user_data.get('patient_id')
    if not patient_id:
        session_data = request.session.get('adminAmendment')
        patient_data = session_data['patient_data']
        patient_id = patient_data.get('patient_id')
    staff_id = selected_slot.get('staff_id')
    appointment_start = selected_slot.get('start_time')
    appointment_date = datetime.strptime(selected_slot.get('date'), "%Y-%m-%d").date()
    is_tuesday_to_thursday = appointment_date.weekday() in [1, 2, 3]
    appointment_end = selected_slot.get('end_time')

    existing_appointments_count = Appointments.objects.filter(  appointment_date=appointment_date,
                                                                appointment_start=appointment_start,
                                                                appointment_end = appointment_end,
                                                                staff_id=selected_slot.get('staff_id')
                                                            ).count()

    if existing_appointments_count == 0 or (is_tuesday_to_thursday and existing_appointments_count < 2):
        appointment = Appointments(
            appointment_status=appointment_status,
            appointment_outcome=appointment_outcome,
            appointment_payment_status=appointment_payment_status,
            patient_id=patient_id,
            staff_id=staff_id,
            appointment_start=appointment_start,
            appointment_end=appointment_end,
            appointment_date=appointment_date,
            consultation_cost=consultation_cost,
        )
        appointment.save()

        return JsonResponse({'status': 'success', 'redirect_url': reverse('patients_appointments:patient_appointment_confirm')})
    else:
        return JsonResponse({'status':'failed', 'redirect_url': reverse('patients_appointments:patient_appointment_fail')})

@never_cache
def patient_appointment_confirm(request):
    if not request.session.get('user_data'):
        return redirect('patient_main')
    elif not request.session.get('selectedSlot'):
        return redirect('patient_main')
    
    user_data = request.session.get('user_data')
    if request.session.get('selectedSlot', {}):
        selected_slot = request.session.get('selectedSlot', {})

        staff_details = Staffs.objects.select_related('user').get(staff_id=selected_slot.get('staff_id'))
        name = staff_details.user.name

        context = {
            'staff_name': "Dr. " + name,
            'selected_type': selected_slot.get('type'),
            'selected_date': selected_slot.get('date'),
            'selected_start_time': selected_slot.get('start_time'),
            'selected_end_time': selected_slot.get('end_time'),
            'selected_duration': selected_slot.get('duration'),
            'user_data': user_data,
        }

        del request.session['selectedSlot']
    else:
        return redirect('patient_main')
    
    if request.session.get('adminAmendment'):
        del request.session['adminAmendment']
        return render(request, 'admin_confirmed.html', context)
    else:
        return render(request, 'appointment_confirmed.html', context)

@never_cache  
def patient_appointment_fail(request):
    if request.session.get('selectedSlot', {}):
        del request.session['selectedSlot']
    else:
        return redirect('patient_main')
    
    return render(request, 'appointment_failed.html')

@require_POST
def clear_amend_item(request):
    data = json.loads(request.body)
    item_key = data.get('item_key')
    if item_key in request.session:
        del request.session[item_key]
        return JsonResponse({'status': 'success', 'message': 'Amend Details Removed'})
    return JsonResponse({'status': 'error', 'message': 'Details not found'})

def update_list(request): #backend calculation code 
    if request.method == 'GET':
        status = request.GET.get('status')
        if not request.session.get('user_data'):
            return redirect('patient_main')
        user_data = request.session.get('user_data')
        user_id = user_data.get('user_id')

        patient = Patients.objects.get(user_id=user_id)
        patient_id = patient.patient_id
     
        if status == 'upcoming':
            now = make_aware(datetime.now())
            appointments = Appointments.objects.filter(
                patient_id=patient_id,
                appointment_status=status,
            ).select_related('staff__user').order_by('-appointment_date', '-appointment_start')
            
            appointments_data = []
            for appointment in appointments:
                appointment_datetime = make_aware(datetime.combine(appointment.appointment_date, appointment.appointment_start))
                is_expired = appointment_datetime < now

                appointment_info = {
                    'appointment_id': appointment.appointment_id,
                    'appointment_date': appointment.appointment_date,
                    'appointment_start': appointment.appointment_start,
                    'appointment_end': appointment.appointment_end,
                    'appointment_status': appointment.appointment_status,
                    'appointment_outcome': appointment.appointment_outcome,
                    'staff_id': appointment.staff_id,
                    'staff__user__role': appointment.staff.user.role,
                    'staff__user__name': appointment.staff.user.name,
                    'status': 0 if not is_expired else 1 
                }
                appointments_data.append(appointment_info)

            return JsonResponse(list(appointments_data), safe=False)
        
        else:
            appointments_data = Appointments.objects.filter(patient_id=patient_id,
                                                appointment_status=status
                                        ).select_related('staff__user' 
                                        ).values(
                                            'appointment_id',
                                            'appointment_date',
                                            'appointment_start',
                                            'appointment_end',
                                            'appointment_status',
                                            'appointment_outcome',
                                            'staff_id',
                                            'staff__user__role',
                                            'staff__user__name',
                                        ).order_by('-appointment_date', '-appointment_start')
                    
            return JsonResponse(list(appointments_data), safe=False)   

def cancel_appointment(request):
    if request.method == 'POST':
        if not request.session.get('user_data'):
            return redirect('patient_main')
        
        appointment_id = int(request.POST.get('id'))
        
        user_data = request.session.get('user_data')
        user_id = user_data.get('user_id')

        patient = Patients.objects.get(user_id=user_id)
        patient_id = patient.patient_id

        try:
            appointment_to_cancel = Appointments.objects.get(patient_id=patient_id, appointment_id=appointment_id)
            appointment_to_cancel.appointment_outcome = 'cancelled'
            appointment_to_cancel.appointment_status = 'cancelled'
            cancel_record, created = AppointmentCancellations.objects.update_or_create(
                appointment=appointment_to_cancel,
                defaults={
                    'description': 'Cancelled by Patient',
                    'cancellation_type_id': 9,
                }
            )

            appointment_to_cancel.save()
            return JsonResponse("Appointment cancelled successfully.", safe=False)
        except ObjectDoesNotExist:
            return JsonResponse("No appointment found with the given details.", safe=False)

def patient_appointments_list(request):

    now = make_aware(datetime.now())

    if request.method == 'GET' and 'status' in request.GET:
        return update_list(request)
    
    if not request.session.get('user_data'):
        return redirect('patient_main')
    
    user_data = request.session.get('user_data')
    user_id = user_data.get('user_id')

    patient = Patients.objects.get(user_id=user_id)
    patient_id = patient.patient_id

    appointments = Appointments.objects.filter(
        patient_id=patient_id,
        appointment_status='upcoming',
    ).select_related('staff__user').order_by('-appointment_date', '-appointment_start')

    appointments_data = []
    for appointment in appointments:
        appointment_datetime = make_aware(datetime.combine(appointment.appointment_date, appointment.appointment_start))
        is_expired = appointment_datetime < now

        appointment_info = {
            'appointment_id': appointment.appointment_id,
            'appointment_date': appointment.appointment_date,
            'appointment_start': appointment.appointment_start,
            'appointment_end': appointment.appointment_end,
            'appointment_status': appointment.appointment_status,
            'appointment_outcome': appointment.appointment_outcome,
            'staff_id': appointment.staff_id,
            'staff__user__role': appointment.staff.user.role,
            'staff__user__name': appointment.staff.user.name,
            'status': 0 if not is_expired else 1 
        }
        appointments_data.append(appointment_info)

    context = {
        'appointments':appointments_data,
        'user_data': user_data,
    }

    response = render(request,'appointments_list.html', context)

    return response

def patient_appointments_invoice(request):
    selected_type = request.GET.get('type')
    selected_date = request.GET.get('date')
    selected_start = request.GET.get('start').replace('.', '')
    selected_end = request.GET.get('end').replace('.', '')
    selected_start_time = datetime.strptime(selected_start, '%H:%M:%S').time()
    formatted_start_time = selected_start_time.strftime('%H:%M')
    selected_end_time = datetime.strptime(selected_end, '%H:%M:%S').time()
    formatted_end_time = selected_end_time.strftime('%H:%M')

    if not request.session.get('user_data'):
        return redirect('patient_main')

    user_data = request.session.get('user_data')
    user_id = user_data.get('user_id')

    patient = Patients.objects.get(user_id=user_id)
    patient_id = patient.patient_id

    invoice_data = Appointments.objects.filter(
                                                patient_id=patient_id,
                                                appointment_date=selected_date,
                                                appointment_start=formatted_start_time,
                                                appointment_end=formatted_end_time,
                                                staff__user__role=selected_type 
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
            "cost": data['consultation_cost']
        }

    response = render(request, 'appointment_invoice.html', appointment_info)

    return response

def patient_appointments_reason(request):
    if not request.session.get('user_data'):
        return redirect('patient_main')

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

    response = render(request, 'appointment_reason.html', appointment_info)

    return response