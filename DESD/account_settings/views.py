import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from database_models.models import *
from datetime import date, datetime
from sign_up.validations import *

def index(request):
  user_data = request.session.get('user_data', {})
  context = {'user_data': user_data,}
  return render(request, 'update.html', context)

def update_record(request):
    user_data = request.session.get('user_data', {})    
    D_user_id = request.session.get('user_id')    
    context = {'user_data': user_data,}
    
    if request.method == 'POST':        
      name = request.POST['name']
      username = request.POST['user']
      psw = request.POST['password']
      confirm_psw = request.POST['password_confirm']    
      postcode = request.POST['pstcde']
      email = request.POST['email']
      address = request.POST['address']
      phone = request.POST['phone']
      date_of_birth = request.POST['dob']      
        
      # Create an empty array for error messages        
      errors = {}
                
      if not validate_username(username):
        errors['username_invalid'] = True
    
      if psw != confirm_psw:
        errors['password_mismatch'] = True
                
      if not validate_password(psw):
        errors['password_invalid'] = True
                
      if not validate_phonenumber(phone):
        errors['phone_invalid'] = True
    
      today = date.today()
      dob_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
      if dob_date > today:
        errors['date_invalid'] = True
    
      if not checking_username(username):
        errors['username_unique'] = True
                  
      if errors:
        print(errors)
              
        context = {
          'user_data': user_data,
          'errors': errors,
        }
            
        messages.error(request, context)
        return render(request, 'update.html', context)
                    
      else:
        # Password matches, proceed with saving changes
        psw = hash_password(psw)
        
        context = {'user_data': user_data,}
    
        user = Users.objects.get(user_id=D_user_id)
                
        user.name = name
        user.username = username
        user.password = psw
        user.postcode = postcode
        user.email = email
        user.address = address
        user.phone_number = phone
        user.date_of_birth = date_of_birth
        print("User Saved") 
        
        user.save()             
        
        return render(request, "update.html", context)    
    return render(request, 'patients_dashboard.html', context)
    
def goback(request):
  user_data = request.session.get('user_data', {})
  id = user_data.get('user_id')
    
  user = Users.objects.get(user_id=id)
    
  if user.role == "admin":
    print("Redirected to Admin Dashboard")
    return redirect('admin_main')
  elif user.role == "patient":
    print("Redirected to Patients Dashboard")
    return redirect('patient_main')
  else:
    print("Redirected to Doctor/Nurse Dashboard")
    return redirect('doctor_nurse_main')

def delete(request): 
  user_data = request.session.get('user_data', {})
  user_id = user_data.get('user_id')  
    
  user = Users.objects.get(user_id=user_id)
  
  print(user.password) 
  if request.method == "POST":
    confirm_password = request.POST['confirm_pass']
    hash_psw = hash_password(confirm_password)
    if user.password == hash_psw:
      user.name = "DELETED USER"
      user.role = "deleted_user"           
      user.username = f"DELETED_USER_#{user.user_id}"
      user.gender = None
      user.date_of_birth = None
      user.email = None
      user.phone_number = None
      user.address = None
      user.postcode = None
      user.is_active = 0
      user.save()
      request.session.flush()
      print("Account Deleted")
      messages.error(request, "Account has been deleted")
      return redirect("/")
    else:
      print("Entered the wrong password")
      return redirect("index")
  return redirect("index")

def extract_data_csv(request):  
  user_data = request.session.get('user_data', {})  
  D_user_id = user_data.get('user_id')
  D_patient_id = user_data.get('patient_id')
  name = user_data.get('name')
    
  try:
    # Retrieve user data
    user = Users.objects.get(user_id=D_user_id)

    # Retrieve appointments assigned to the user
    appointments = Appointments.objects.filter(patient_id=D_patient_id)

    # Retrieve prescriptions assigned to the user
    prescriptions = PrescriptionsAssignments.objects.filter(appointment__patient_id=D_patient_id)

  except (Users.DoesNotExist, Appointments.DoesNotExist, PrescriptionsAssignments.DoesNotExist) as e:
    # Handle case where data does not exist
    return HttpResponse("Data not found.")

  # Prepare user data for CSV
  user_csv_data = [
    {
      "id": user.user_id,
      "name": user.name,
      "role": user.role,
      "username": user.username,
      "gender": user.gender,
      "date_of_birth": user.date_of_birth.strftime('%Y-%m-%d'),  # Format date as string
      "email": user.email,
      "phone_num": user.phone_number,
      "address": user.address,
    }
  ]

  # Prepare appointments data for CSV
  appointments_csv_data = [
    {
      "appointment_id": appointment.appointment_id,
      "date": appointment.appointment_date,
      "start_time": appointment.appointment_start,
      "end_time": appointment.appointment_end,
      "consultation_cost": appointment.consultation_cost,
      "status": appointment.appointment_status,
    }
    for appointment in appointments
  ]

  # Prepare prescriptions data for CSV
  prescriptions_csv_data = [
    {
      "prescription_id": prescription.prescription_assignment_id,
      "cost": prescription.prescription_cost,
      "prescription_status": prescription.prescription_status,
      "issued_date": prescription.issued_date,
      "quantity": prescription.quantity,
      "collection_status": prescription.collection_status,
    }
    for prescription in prescriptions
  ]

  # Create CSV response
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = f'attachment; filename="{name}_data.csv"'

  # Write user data to CSV
  writer = csv.DictWriter(response, fieldnames=["id", "name", "role", "username", "gender", "date_of_birth", "email", "phone_num", "address"])
  writer.writeheader()
  for data in user_csv_data:
    writer.writerow(data)

  # Add spacing between sections
  writer.writerow({})

  # Write appointments data to CSV
  writer = csv.DictWriter(response, fieldnames=["appointment_id", "date", "start_time", "end_time", "consultation_cost", "status"])
  writer.writeheader()
  for data in appointments_csv_data:
    writer.writerow(data)

  # Add spacing between sections
  writer.writerow({})

  # Write prescriptions data to CSV
  writer = csv.DictWriter(response, fieldnames=["prescription_id", "cost", "prescription_status", "issued_date", "quantity", "collection_status"])
  writer.writeheader()
  for data in prescriptions_csv_data:
    writer.writerow(data)

  return response