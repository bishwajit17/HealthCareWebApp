from datetime import datetime
from decimal import Decimal
from django.forms import ValidationError
from django.shortcuts import render, redirect
from django.db.models import Sum, F, Q, ExpressionWrapper
from django.contrib import messages
from database_models.models import *
from DESD.views import verify_user_role

def admin_report(request):
  user_data = request.session.get('user_data', {})
  
  if not verify_user_role(user_data.get('role'), 'admin'):
    return redirect('/')
  
  today_date = datetime.now().date()
  today_date_str = today_date.strftime('%Y-%m-%d')

  print(today_date_str)
  
  context = {
    'user_data': user_data,
    'today_date': today_date_str,
  }
    
  if request.method == 'POST':
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    # Parse start_date and end_date from strings to datetime objects
    try:
      start_date = datetime.strptime(start_date, '%Y-%m-%d')
      end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
      raise ValidationError('Invalid date format. Please use YYYY-MM-DD.')
        
    # Server-side validation to prevent future dates and end date before start date
    if start_date > end_date:
      messages.error(request, "End date should be after start date.")
      return render(request, 'admin_report.html', context)
    
    if end_date.date() > datetime.now().date():
      messages.error(request, "End date should not be in the future.")
      return render(request, 'admin_report.html', context)
        
    ##### Turnover Report
    # Retrieve data from the database based on selected dates
    appointments = Appointments.objects.filter(appointment_date__range=(start_date, end_date))
    patients = Patients.objects.filter(appointments__in=appointments, user__is_active=1).distinct()
    prescriptions = PrescriptionsAssignments.objects.filter(appointment__appointment_date__range=(start_date, end_date))
    
    print(Appointments.objects.filter(appointment_date__range=(start_date, end_date)).values('appointment_date'))
    print(Appointments.objects.filter(appointment_date__range=(start_date, end_date)).values('consultation_cost')) 
    print(Appointments.objects.filter(appointment_date__range=(start_date, end_date)).aggregate(total_cost=Sum('consultation_cost')))   
    totalPatientPaid = Appointments.objects.filter(appointment_date__range=(start_date, end_date)).aggregate(Sum('consultation_cost'))
    print(totalPatientPaid['consultation_cost__sum'])
    # total_patient_paid = totalPatientPaid['consultation_cost__sum']
      # Get the total hours worked for doctors and nurses
    ##### Charges Report
    # Create a list to store patient names, payment_source, their total cost, and staff assigned to them
    patient_costs = []
    for patient in patients:            
      appointment_costs = appointments.filter(patient=patient).aggregate(total_cost=Sum('consultation_cost'))
      prescription_costs = PrescriptionsAssignments.objects.filter(appointment__in=appointments, appointment__patient=patient).aggregate(total_cost=Sum('prescription_cost'))
      total_cost = (appointment_costs['total_cost'] or 0) + (prescription_costs['total_cost'] or 0)      
      staff_assigned = Staffs.objects.filter(appointments__in=appointments, appointments__patient=patient).distinct()
      patient_costs.append((patient.user.name, patient.payment_source, total_cost, staff_assigned))     
        
    #### Expenses Report         
    # Get the Doctor's and Nurse's Hourly Rate
    doctor_hourly_rate = Staffs.objects.filter(Q(user__role='doctor') | Q(user__role='nurse')).first().staff_rate.wage_per_hr
    # Calculate the total duration of appointments in hours
    appointment_duration_in_hours = ExpressionWrapper(F('appointment_end') - F('appointment_start'), output_field=models.DurationField())
    # Filter appointments for doctors and nurses within the date range and calculate total hours worked
    doctor_appointments = Appointments.objects.filter(Q(staff__user__role='doctor') | Q(staff__user__role='nurse'),appointment_date__range=[start_date, end_date]).annotate(duration_in_hours=appointment_duration_in_hours).aggregate(total_hours_worked=Sum('duration_in_hours'))
    # Get the staff's hour type (full-time or part-time)
    hour_type = Staffs.objects.filter(Q(user__role='doctor') | Q(user__role='nurse')).first().hour_type
    
    # Calculate the total salary for doctors and nurses based on their hour type
    if doctor_appointments['total_hours_worked']:
      if hour_type == 'full':
        # Full-time staff work 8 hours per day
        total_doctor_salary = (Decimal(doctor_appointments['total_hours_worked'].total_seconds()) / Decimal(3600)) * Decimal(doctor_hourly_rate) * 8
      elif hour_type == 'part':
        # Part-time staff work 4 hours per day
        total_doctor_salary = (Decimal(doctor_appointments['total_hours_worked'].total_seconds()) / Decimal(3600)) * Decimal(doctor_hourly_rate) * 4
      else:
        total_doctor_salary = Decimal(0)  # Handle other cases if necessary
    else:
      total_doctor_salary = Decimal(0)
      
    # Calculate total money received from appointments
    total_appointment_fees = Appointments.objects.filter(appointment_date__range=[start_date, end_date]).aggregate(total_consultation_fees=Sum('consultation_cost'))['total_consultation_fees'] or Decimal(0)
    # Calculate total money received from prescriptions
    total_prescription_fees = PrescriptionsAssignments.objects.filter(issued_date__range=[start_date, end_date]).aggregate(total_prescription_cost=Sum('prescription_cost'))['total_prescription_cost'] or Decimal(0)
    # Calculate the total money received from patients
    total_money_received = total_appointment_fees + total_prescription_fees
    # Calculate profit
    profit = total_money_received - total_doctor_salary

    # Debugging prints
    print("Total Doctor and Nurse Salary:", total_doctor_salary)
    print("Total Money Received from Patients:", total_money_received)
    print("Profit:", profit)
    
    print(start_date)
    print(end_date)
                
    context = {
      'user_data': user_data,
      'start_date': start_date,
      'end_date': end_date,
      'appointments_count': appointments.count(),
      'patients_count': patients.count(),
      'prescriptions_count': prescriptions.count(),
      'patient_costs': patient_costs,
      'total_patient_paid': totalPatientPaid['consultation_cost__sum'],    
      'doctor_salary': round(total_doctor_salary, 2),
      'total_cost': round(total_money_received, 2),
      'profit': round(profit, 2),
      'today_date': today_date_str,
    }            
    return render(request, "admin_report.html", context)      
  return render(request, "admin_report.html", context)