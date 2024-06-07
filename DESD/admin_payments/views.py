import csv
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from database_models.models import *
from django.db.models import Q
from DESD.views import verify_user_role

def admin_payment(request):
    user_data = request.session.get('user_data', {})
    
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')
    
    patients = Patients.objects.filter(user__is_active=1)       
    prescriptions = PrescriptionsAssignments.objects.filter(~Q(collection_status='cancelled'))
    appointments = Appointments.objects.filter(~Q(appointment_status='cancelled'))
    #prescriptions = PrescriptionsAssignments.objects.all()
    #appointments = Appointments.objects.all()

    context = {
      'patients': patients,    
      'appointments': appointments,
      'prescriptions': prescriptions,
      'user_data': user_data,
    }
    return render(request, "admin_payment.html", context)
  
def presc_mark_paid(request, id):
  try:
    # Retrieve the prescription object based on the prescription_id
    prescription = PrescriptionsAssignments.objects.get(prescription_assignment_id=id)
        
    # Update the prescription payment status to 2
    prescription.prescription_payment_status = 2
    prescription.save()
        
    print(f"Prescription with ID {id} marked as paid and sent to NHS successfully.")
  except PrescriptionsAssignments.DoesNotExist:
    # Handle the case where the prescription with the given ID does not exist
    print(f"Prescription with ID {id} does not exist.")
  except Exception as e:
    # Handle any other errors that occur during the update process
    print(f"Error marking prescription with ID {id} as paid and sending to NHS: {e}")
  
  return redirect("admin_payment")

def appoint_mark_paid(request, id):
  try:
    # Retrieve the prescription object based on the prescription_id
    appointment = Appointments.objects.get(appointment_id=id)
        
    # Update the prescription payment status to 1
    appointment.appointment_payment_status = 1
    appointment.save()
        
    print(f"Appointment with ID {id} marked as paid and sent to NHS successfully.")
  except PrescriptionsAssignments.DoesNotExist:
    # Handle the case where the prescription with the given ID does not exist
    print(f"Appointment with ID {id} does not exist.")
  except Exception as e:
    # Handle any other errors that occur during the update process
    print(f"Error marking appointment with ID {id} as paid and sending to NHS: {e}")
  
  return redirect("admin_payment")

def presc_mark_all_paid(request):
  try:
    data = json.loads(request.body)
    patient_id = data.get('patient_id')
    if patient_id:
      # Retrieve prescriptions for the given patient
      prescriptions = PrescriptionsAssignments.objects.filter(appointment__patient_id=patient_id)            
      # Update payment status for all prescriptions
      prescriptions.update(prescription_payment_status=2)            
      return JsonResponse({'success': True})
    else:
      raise ValueError('Patient ID not provided.')
  except Exception as e:
    return JsonResponse({'success': False, 'error': str(e)}, status=500)

def appoint_mark_all_paid(request):
  try:
    data = json.loads(request.body)
    patient_id = data.get('patient_id')
    if patient_id:
      # Retrieve appointments for the given patient
      appointments = Appointments.objects.filter(patient_id=patient_id)            
      # Update payment status for all appointments
      appointments.update(appointment_payment_status=1)            
      return JsonResponse({'success': True})
    else:
      raise ValueError('Patient ID not provided.')
  except Exception as e:
    return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
def payments_extract_data(request):
  user_data = request.session.get('user_data', {})  
  name = user_data.get('name')
    
  try:       
    prescriptions = PrescriptionsAssignments.objects.all()
    appointments = Appointments.objects.all()

  except (Users.DoesNotExist, Appointments.DoesNotExist, PrescriptionsAssignments.DoesNotExist) as e:
    # Handle case where data does not exist
    return HttpResponse("Data not found.")

  # Prepare user data for CSV
  prescriptions_csv_data = [
    {
      "id": prescription.prescription_assignment_id,
      "issued_date": prescription.issued_date,
      "name": prescription.prescription.prescription_name,
      "assigned_to": prescription.appointment.patient.user.name,
      "quantity": prescription.quantity,
      "cost": prescription.prescription_cost,
      "payment_status": prescription.prescription_payment_status,
    }
    for prescription in prescriptions
  ]

  # Prepare appointments data for CSV
  appointments_csv_data = [
    {
      "appointment_id": appointment.appointment_id,
      "staff_name": appointment.staff.user.name,
      "staff_type": appointment.staff.user.role,
      "date": appointment.appointment_date,
      "start_time": appointment.appointment_start,
      "end_time": appointment.appointment_end,
      "cost": appointment.consultation_cost,
      "payment_status": appointment.appointment_payment_status,
    }
    for appointment in appointments
  ]

  # Create CSV response
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = f'attachment; filename="{name}_data.csv"'

  # Write user data to CSV
  writer = csv.DictWriter(response, fieldnames=["id", "issued_date", "name", "assigned_to", "quantity", "cost", "payment_status"])
  writer.writeheader()
  for data in prescriptions_csv_data:
    writer.writerow(data)

  # Add spacing between sections
  writer.writerow({})

  # Write appointments data to CSV
  writer = csv.DictWriter(response, fieldnames=["appointment_id", "staff_name", "staff_type", "date", "start_time", "end_time", "cost", "payment_status"])
  writer.writeheader()
  for data in appointments_csv_data:
    writer.writerow(data)

  return response