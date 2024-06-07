from django.shortcuts import render
import csv
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
import re
from django.urls import reverse
from passlib.hash import sha256_crypt
import hashlib
from django.contrib import messages
from database_models.models import Users, Patients
from datetime import date, datetime
from django.db.models import Q
from django.template import loader
from sign_up.validations import *
from DESD.views import verify_user_role

# def signup(request):
#     return render(request, 'signupPage.html')

class Admins():
    pass

def patientDetails(request):
    user_data = request.session.get('user_data', {})
    name = user_data.get('name')  
    # print(user_data) 
    # print(name) 
    
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')

    patientUser = Users.objects.filter(role='patient').values('user_id','name','role','username','gender','date_of_birth', 'email', 'phone_number', 'address', 'postcode')
    context={
        'patientDetails':patientUser,
        'user_data': user_data,
    }
    
    return render(request, 'patientDetails.html', context)

# Create your views here.
def patient_signup(request):
    print("testing", request.method)
    print("here 1")
    user_data = request.session.get('user_data', {})
    name = user_data.get('name') 
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        phnumber = request.POST.get('telnum')
        email = request.POST.get('email')
        username = request.POST.get('username')
        pwd = request.POST.get('password')
        confpwd = request.POST.get('passwordConfirm')
        paymentType = request.POST.get('paymentType')

        
        
        errors = {}  # Create an empty array for error messages
        
        
        if not validate_username(username):
            errors['username_invalid'] = True

        if pwd != confpwd:
            errors['password_mismatch'] = True
        
        if not validate_password(pwd):
            errors['password_invalid'] = True
            
        if not validate_phonenumber(phnumber):
            errors['phone_invalid'] = True

        today = date.today()
        dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
        if dob_date > today:
            errors['date_invalid'] = True

        if not checking_username(username):
            errors['username_unique'] = True
        
        if errors:
            print(errors)
            context = {
                            'fullname': fullname,
                            'username': username,
                            'dob': dob,
                            'gender':gender,
                            'address': address,
                            'postcode': postcode,
                            'email': email,
                            'phnumber': phnumber,
                            'paymentType': paymentType,
                            'errors': errors,
                        }
            # messages.error(request, context)
            return render(request, 'patient_signup.html', context)
            # return redirect('/signup_page',context)
        else:
            hashed_pwd = hash_password(pwd)  # Hash the password
            user = Users(
                name=fullname,
                role='patient',
                gender=gender,
                username=username,
                password=hashed_pwd,
                date_of_birth=dob,
                address=address,
                postcode=postcode,
                phone_number=phnumber,
                email=email,
            )
            print(user.name)
            user.save()

            new_user = Users.objects.get(username=username)

            patient = Patients(
                user_id=new_user.user_id,
                payment_source=paymentType,
            )

            patient.save()

            return redirect('patientDetails')
    context={
        'user_data': user_data,
    }
        
    return render(request, 'patient_signup.html',context)


def deletePatient(request): 
  
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_data = request.session.get('user_data', {})
        
        hashed_pwd = hash_password(password)
        D_id = user_data.get('user_id')
        userAdmin = Users.objects.get(user_id=D_id)
        print(userAdmin.name)
        user = Users.objects.get(username=username)
        print(user.name,user.user_id)
        userId = user.user_id

        patientDetail = Patients.objects.get(user_id=userId)
        print(patientDetail.patient_id)
        adminPassword = userAdmin.password
        if adminPassword == hashed_pwd:
            user.name = "DELETED USER"
            user.role = "deleteduser"
            user.username = f"DELETED_USER#{user.user_id}"
            user.gender = None
            user.date_of_birth = None
            user.email = None
            user.phone_number = None
            user.address = None
            user.postcode = None
            user.is_active = 0
            user.save()
            print("success msg")
            return redirect('patientDetails')
        else:
            messages.error(request, 'Incorrect Password. Please try Again.')
            print("admin password incorrect")
            return redirect('patientDetails')

def editPatient(request, user_id, dates):
    user_data = request.session.get('user_data', {})
    user= Users.objects.get(user_id=user_id)
    patient = Patients.objects.get(user_id=user_id)
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')
    print("testing", request.method)
    if request.method == 'POST':

        print("testing", request.method)
        fullname = request.POST.get('fullname')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        phnumber = request.POST.get('telnum')
        email = request.POST.get('email')
        username = request.POST.get('username')
        pwd = request.POST.get('password')
        confpwd = request.POST.get('passwordConfirm')
        paymentType = request.POST.get('paymentType')

        if pwd.strip() == '' or confpwd.strip() == '':
            errors = {}  # Create an empty array for error messages
        
            if user.username == username:
                if not validate_phonenumber(phnumber):
                    errors['phone_invalid'] = True

                today = date.today()
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
                if dob > today:
                    errors['date_invalid'] = True

                if errors:
                    print(errors)
                    context = {
                                    'fullname': fullname,
                                    'username': username,
                                    'dob': dob,
                                    'gender':gender,
                                    'address': address,
                                    'postcode': postcode,
                                    'email': email,
                                    'phnumber': phnumber,
                                    'paymentType': paymentType,
                                    'errors': errors,
                                }
                    return render(request, 'patient_signup.html', context)
                else:
                    user.name = fullname
                    user.gender = gender
                    user.date_of_birth = dob
                    user.address = address
                    user.postcode = postcode
                    user.phone_number = phnumber
                    user.email = email
                    patient.payment_source= paymentType
                    user.save()
                    patient.save()

                    print("success full  updated without updating username")
                    return redirect('patientDetails')
            else:
                if not validate_username(username):
                    errors['username_invalid'] = True

                if not validate_phonenumber(phnumber):
                    errors['phone_invalid'] = True

                today = date.today()
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
                if dob > today:
                    errors['date_invalid'] = True

                if not checking_username(username):
                    errors['username_unique'] = True
                if errors:
                    print(errors)
                    context = {
                                    'fullname': fullname,
                                    'username': username,
                                    'dob': dob,
                                    'gender':gender,
                                    'address': address,
                                    'postcode': postcode,
                                    'email': email,
                                    'phnumber': phnumber,
                                    'paymentType': paymentType,
                                    'mode' : 'edit',
                                    'errors': errors,
                                }
                    return render(request, 'staffSignUpPage.html', context)
                else:
                    user.username = username
                    user.name = fullname
                    user.gender = gender
                    user.date_of_birth = dob
                    user.address = address
                    user.postcode = postcode
                    user.phone_number = phnumber
                    user.email = email
                    patient.payment_source= paymentType
                    user.save()
                    patient.save()
                    print("successuflly update with username as well")
                    return redirect('patientDetails')
        if pwd.strip() != '' and user.username == username:
            print(pwd, confpwd)
            print('testing 1')
            errors = {}
            if pwd != confpwd:
                errors['password_mismatch'] = True
            
            if not validate_password(pwd):
                errors['password_invalid'] = True
            if errors:
                print(errors)
                context = {
                                    'fullname': fullname,
                                    'username': username,
                                    'dob': dob,
                                    'gender':gender,
                                    'address': address,
                                    'postcode': postcode,
                                    'email': email,
                                    'phnumber': phnumber,
                                    'paymentType': paymentType,
                                    'mode' : 'edit',
                                    'errors': errors,
                                }
                return render(request, 'staffSignUpPage.html', context)
            else:
                print("No errors, processing the data")
                hashed_pwd = hash_password(pwd)
                user.name = fullname
                user.gender = gender
                user.date_of_birth = dob
                user.password = hashed_pwd
                user.address = address
                user.postcode = postcode
                user.phone_number = phnumber
                user.email = email
                patient.payment_source= paymentType
                user.save()
                patient.save()
                print("Edit patient password only without editing username")
                return redirect('patientDetails')
        elif pwd.strip() != '' and user.username != username:
            errors ={}
            if not validate_username(username):
                errors['username_invalid'] = True

            if pwd != confpwd:
                errors['password_mismatch'] = True
            
            if not validate_password(pwd):
                errors['password_invalid'] = True
                
            if not validate_phonenumber(phnumber):
                errors['phone_invalid'] = True

            today = date.today()
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            if dob_date > today:
                errors['date_invalid'] = True

            if not checking_username(username):
                errors['username_unique'] = True

            if errors:
                print(errors)
                context = {
                            'fullname': fullname,
                            'username': username,
                            'dob': dob,
                            'gender':gender,
                            'address': address,
                            'postcode': postcode,
                            'email': email,
                            'phnumber': phnumber,
                            'paymentType': paymentType,
                            'mode' : 'edit',
                            'errors': errors,
                            }
                # messages.error(request, context)
                return render(request, 'patient_signup.html', context)
            else:

                hashed_pwd = hash_password(pwd)  # Hash the password
                # hashed_pwd = hash_password(pwd)
                user.name = fullname
                user.username = username
                user.gender = gender
                user.date_of_birth = dob
                user.password = hashed_pwd
                user.address = address
                user.postcode = postcode
                user.phone_number = phnumber
                user.email = email
                patient.payment_source= paymentType
                print(user.name)
                user.save()
                patient.save()

                return redirect('patientDetails')

    
    context = {
                            'fullname': user.name,
                            'username': user.username,
                            'gender' : user.gender,
                            'dob': dates,
                            'address': user.address,
                            'postcode': user.postcode,
                            'email': user.email,
                            'phnumber': user.phone_number,
                            'paymentType': patient.payment_source,
                            'user_data': user_data,
                            'mode' : 'edit'
                            
                        }

    print(context)
    return render(request, 'patient_signup.html', context)


def extract_data(request):
    # Retrieve user data from session
    user_data = request.session.get('user_data', {})  
    name = user_data.get('name')
    
    # Filter users based on roles (doctor or nurse)
    users = Users.objects.filter(role__in=['patient'])
    

    # Prepare user data for CSV
    user_csv_data = []
    for user in users:
        user_csv_data.append({
            "id": user.user_id,
            "name": user.name,
            "role": user.role,
            "username": user.username,
            "gender": user.gender,
            "date_of_birth": user.date_of_birth.strftime('%Y-%m-%d'),  # Format date as string
            "email": user.email,
            "phone_num": user.phone_number,
            "address": user.address,            
        })

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{name}_data.csv"'

    # Write user data to CSV
    writer = csv.DictWriter(response, fieldnames=["id", "name", "role", "username", "gender", "date_of_birth", "email", "phone_num", "address"])
    writer.writeheader()
    for data in user_csv_data:
        writer.writerow(data)

    return response