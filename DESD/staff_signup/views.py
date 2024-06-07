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
from django.shortcuts import redirect, get_object_or_404
from sign_up.validations import *
from DESD.views import verify_user_role

# def signup(request):
#     return render(request, 'signupPage.html')

class Admins():
    pass

def staffDetail(request):
    user_data = request.session.get('user_data', {})
    name = user_data.get('name')    
    
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')

    staffUser = Users.objects.filter(Q(role='doctor') | Q(role='nurse') | Q(role='admin')).values('user_id','name','role','username','gender','date_of_birth', 'email', 'phone_number', 'address', 'postcode')
    context={
        'staffdetails':staffUser,
        'user_data': user_data,
    }
    
    return render(request, 'staffDetails.html', context)


def staff_signup(request):
    print("testing", request.method)
    print("here 1")
    user_data = request.session.get('user_data', {})
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')
    if request.method == 'POST':

        fullname = request.POST.get('fullname')
        gender = request.POST.get('gender')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        dob = request.POST.get('dob')
        phnumber = request.POST.get('telnum')
        email = request.POST.get('email')
        username = request.POST.get('username')
        pwd = request.POST.get('password')
        confpwd = request.POST.get('passwordConfirm')
        usertype = request.POST.get('userTypeOptions')
        hourtype = request.POST.get('hourTypeOptions')
        mon = request.POST.get('mon')
        tue = request.POST.get('tue')
        wed = request.POST.get('wed')
        thu = request.POST.get('thu')
        fri = request.POST.get('fri')



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
        if mon is None:
            mon = False
        if tue is None:
            tue = False
        if wed is None:
            wed = False
        if thu is None:
            thu = False
        if fri is None:
            fri = False

        if errors:
            print(errors)
            print(mon,tue,wed,thu,fri)
            context = {
                            'fullname': fullname,
                            'username': username,
                            'gender' : gender,
                            'dob': dob,
                            'mon':mon,
                            'tue':tue,
                            'wed':wed,
                            'thu':thu,
                            'fri':fri,
                            'address': address,
                            'postcode': postcode,
                            'email': email,
                            'phnumber': phnumber,
                            'userTypeOptions': usertype,
                            'hourTypeOptions' : hourtype,
                            'mode' : 'signUp',
                            'errors': errors,
                        }
            # messages.error(request, context)
            return render(request, 'staffSignUpPage.html', context)
        else:

            hashed_pwd = hash_password(pwd)
            user = Users(
                name=fullname,
                role=usertype,
                gender= gender,
                username=username,
                password=hashed_pwd,
                date_of_birth=dob,
                address=address,
                postcode=postcode,
                phone_number=phnumber,
                email=email,
            )
            print(usertype)
            user.save()
            new_user = Users.objects.get(username=username)
            if mon == False:
                mon = 0
            if tue == False:
                tue = 0
            if wed == False:
                wed = 0
            if thu == False:
                thu = 0
            if fri == False:
                fri = 0
            if usertype == "doctor":
                usertype = int(1)
            if usertype == "nurse":
                usertype = int(2)
            if usertype == "admin":
                usertype = int(3)

            staff = Staffs(
                hour_type = hourtype,
                monday = mon,
                tuesday= tue,
                wednesday = wed,
                thursday =thu,
                friday = fri,
                staff_rate_id = usertype,
                user_id = new_user.user_id,
            )
            
            staff.save()
            # # print(new_user.user_id)
            # staffUser = Users.objects.filter(Q(role='doctor') | Q(role='nurse')).values('user_id','name','role','username','gender','date_of_birth', 'email', 'phone_number', 'address', 'postcode')
            # context={
            # 'staffdetails':staffUser
            # }
            print(fullname,gender,address,postcode,dob,username,email,phnumber,usertype,hourtype,pwd,confpwd,mon,tue,wed,thu,fri)
            return redirect('staffDetail')
    context={
        'user_data': user_data,
    }
    return render(request, 'staffSignUpPage.html', context)

def deleteStaff(request):
  print("here") 
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

    staffDetail = Staffs.objects.get(user_id=userId)
    print(staffDetail.staff_id, staffDetail.friday)
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
        return redirect('staffDetail')
    else:
        messages.error(request, 'Incorrect Password. Please try Again.')
        return redirect('staffDetail')

def editStaff(request, user_id, dates):
    
    user_data = request.session.get('user_data', {})
    if not verify_user_role(user_data.get('role'), 'admin'):
      return redirect('/')
    user= Users.objects.get(user_id=user_id)
    staff = Staffs.objects.get(user_id=user_id)
    staffRateId = 0
    monday =0
    tuesday=0
    wednesday=0
    thursday=0
    friday=0
    if staff.monday == True:
        monday = 1
    if staff.tuesday == True:
        tuesday = 1
    if staff.wednesday == True:
        wednesday = 1
    if staff.thursday == True:
        thursday = 1
    if staff.friday == True:
        friday = 1    
    
    print("testing", request.method)
    print("test1")
    if request.method == 'POST':
        print("test2")
        fullname = request.POST.get('fullname')
        gender = request.POST.get('gender')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        dob = request.POST.get('dob')
        phnumber = request.POST.get('telnum')
        email = request.POST.get('email')
        username = request.POST.get('username')
        pwd = request.POST.get('password')
        confpwd = request.POST.get('passwordConfirm')
        usertype = request.POST.get('userTypeOptions')
        hourtype = request.POST.get('hourTypeOptions')
        mon = request.POST.get('mon')
        tue = request.POST.get('tue')
        wed = request.POST.get('wed')
        thu = request.POST.get('thu')
        fri = request.POST.get('fri')
        print(mon,tue,wed,thu,fri)
        print("test3")
        if pwd.strip() == '' and confpwd.strip() == '':
            errors = {}  # Create an empty array for error messages

            if user.username == username:
                if not validate_phonenumber(phnumber):
                    errors['phone_invalid'] = True

                today = date.today()
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
                if dob > today:
                    errors['date_invalid'] = True

                if mon == None:
                    mon = False
                if tue == None:
                    tue = False
                if wed == None:
                    wed = False
                if thu == None:
                    thu = False
                if fri == None:
                    fri = False

                print(mon,tue,wed,thu,fri)
                if errors:
                    print(errors)
                    print(mon,tue,wed,thu,fri)
                    context = {
                                    'fullname': fullname,
                                    'username': username,
                                    'gender' : gender,
                                    'dob': dob,
                                    'mon':mon,
                                    'tue':tue,
                                    'wed':wed,
                                    'thu':thu,
                                    'fri':fri,
                                    'address': address,
                                    'postcode': postcode,
                                    'email': email,
                                    'phnumber': phnumber,
                                    'userTypeOptions': usertype,
                                    'hourTypeOptions' : hourtype,
                                    'mode' : 'edit',
                                    'errors': errors,
                                }
                    return render(request, 'staffSignUpPage.html', context)
                else:

                    print(mon,tue,wed,thu,fri)
                    user.name = fullname
                    user.role = usertype
                    user.gender = gender
                    user.date_of_birth = dob
                    user.address = address
                    user.postcode = postcode
                    user.phone_number = phnumber
                    user.email = email
                    user.save()

                    if usertype == "doctor":
                        staffRateId = 1
                    if usertype == "nurse":
                        staffRateId = 2
                    if usertype == "admin":
                        staffRateId = 3

                    staff.hour_type = hourtype
                    staff.monday = mon
                    staff.tuesday = tue
                    staff.wednesday = wed
                    staff.thursday = thu
                    staff.friday = fri
                    staff.staff_rate_id = staffRateId
                    print(fullname,gender,address,postcode,dob,username,email,phnumber,usertype,hourtype,pwd,confpwd,mon,tue,wed,thu,fri)
                    print('testingfinal')
                    staff.save()

                    print("success full  updated without updating username")
                    # staffUser = Users.objects.filter(Q(role='doctor') | Q(role='nurse')).values('user_id','name','role','username','gender','date_of_birth', 'email', 'phone_number', 'address', 'postcode')
                    # context={
                    # 'staffdetails':staffUser
                    # }
                    print(fullname,gender,address,postcode,dob,username,email,phnumber,usertype,hourtype,pwd,confpwd,mon,tue,wed,thu,fri)
                    return redirect('staffDetail')
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

                if mon is None:
                    mon = False
                if tue is None:
                    tue = False
                if wed is None:
                    wed = False
                if thu is None:
                    thu = False
                if fri is None:
                    fri = False

                if errors:
                    print(errors)
                    print(mon,tue,wed,thu,fri)
                    context = {
                                    'fullname': fullname,
                                    'username': username,
                                    'gender' : gender,
                                    'dob': dob,
                                    'mon':mon,
                                    'tue':tue,
                                    'wed':wed,
                                    'thu':thu,
                                    'fri':fri,
                                    'address': address,
                                    'postcode': postcode,
                                    'email': email,
                                    'phnumber': phnumber,
                                    'userTypeOptions': usertype,
                                    'hourTypeOptions' : hourtype,
                                    'mode' : 'edit',
                                    'errors': errors,
                                }
                    return render(request, 'staffSignUpPage.html', context)
                else:
                    user.name = fullname
                    user.role = usertype
                    user.gender = gender
                    user.date_of_birth = dob
                    user.username=username
                    user.address = address
                    user.postcode = postcode
                    user.phone_number = phnumber
                    user.email = email
                    user.save()
                    
                    if usertype == "doctor":
                        staffRateId = 1
                    if usertype == "nurse":
                        staffRateId = 2
                    if usertype == "admin":
                        staffRateId = 3

                    staff.hour_type = hourtype
                    staff.monday = mon
                    staff.tuesday = tue
                    staff.wednesday = wed
                    staff.thursday = thu
                    staff.friday = fri
                    staff.staff_rate_id = staffRateId
                    staff.save()
                    print("successuflly update with username as well")
                    print(fullname,gender,address,postcode,dob,username,email,phnumber,usertype,hourtype,pwd,confpwd,mon,tue,wed,thu,fri)
                    return redirect('staffDetail')
        if pwd.strip() != '' and user.username == username:
            print(pwd, confpwd)
            print('testing 1')
            errors = {}
            if pwd != confpwd:
                errors['password_mismatch'] = True
            
            if not validate_password(pwd):
                errors['password_invalid'] = True
            if mon is None:
                mon = False
            if tue is None:
                tue = False
            if wed is None:
                wed = False
            if thu is None:
                thu = False
            if fri is None:
                fri = False
            if errors:
                print(errors)
                print(mon,tue,wed,thu,fri)
                context = {
                                    'fullname': fullname,
                                    'username': username,
                                    'gender' : gender,
                                    'dob': dob,
                                    'mon':mon,
                                    'tue':tue,
                                    'wed':wed,
                                    'thu':thu,
                                    'fri':fri,
                                    'address': address,
                                    'postcode': postcode,
                                    'email': email,
                                    'phnumber': phnumber,
                                    'userTypeOptions': usertype,
                                    'hourTypeOptions' : hourtype,
                                    'mode' : 'edit',
                                    'errors': errors,
                                }
                return render(request, 'staffSignUpPage.html', context)
            else:
                print("No errors, processing the data")
                hashed_pwd = hash_password(pwd)
                user.name = fullname
                user.role = usertype
                user.gender = gender
                user.date_of_birth = dob
                user.password = hashed_pwd
                user.address = address
                user.postcode = postcode
                user.phone_number = phnumber
                user.email = email
                user.save()
                    
                if usertype == "doctor":
                        staffRateId = 1
                if usertype == "nurse":
                    staffRateId = 2
                if usertype == "admin":
                        staffRateId = 3

                staff.hour_type = hourtype
                staff.monday = mon
                staff.tuesday = tue
                staff.wednesday = wed
                staff.thursday = thu
                staff.friday = fri
                staff.staff_rate_id = staffRateId
                staff.save()
                staffUser = Users.objects.filter(Q(role='doctor') | Q(role='nurse')).values('user_id','name','role','username','gender','date_of_birth', 'email', 'phone_number', 'address', 'postcode')
                context={
                    'staffdetails':staffUser
                    }
                print('only password change')
                print(fullname,gender,address,postcode,dob,username,email,phnumber,usertype,hourtype,pwd,confpwd,mon,tue,wed,thu,fri)
                return redirect('staffDetail')
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
            if mon is None:
                mon = False
            if tue is None:
                tue = False
            if wed is None:
                wed = False
            if thu is None:
                thu = False
            if fri is None:
                fri = False

            if errors:
                print(errors)
                print(mon,tue,wed,thu,fri)
                context = {
                                'fullname': fullname,
                                'username': username,
                                'gender' : gender,
                                'dob': dob,
                                'mon':mon,
                                'tue':tue,
                                'wed':wed,
                                'thu':thu,
                                'fri':fri,
                                'address': address,
                                'postcode': postcode,
                                'email': email,
                                'phnumber': phnumber,
                                'userTypeOptions': usertype,
                                'hourTypeOptions' : hourtype,
                                'mode' : 'signUp',
                                'errors': errors,
                            }
                # messages.error(request, context)
                return render(request, 'staffSignUpPage.html', context)
            else:

                hashed_pwd = hash_password(pwd)
                user.name = fullname
                user.role = usertype
                user.gender = gender
                user.username = username
                user.date_of_birth = dob
                user.password = hashed_pwd
                user.address = address
                user.postcode = postcode
                user.phone_number = phnumber
                user.email = email
                user.save()
                    
                if usertype == "doctor":
                        staffRateId = 1
                if usertype == "nurse":
                    staffRateId = 2
                if usertype == "admin":
                        staffRateId = 3

                staff.hour_type = hourtype
                staff.monday = mon
                staff.tuesday = tue
                staff.wednesday = wed
                staff.thursday = thu
                staff.friday = fri
                staff.staff_rate_id = staffRateId
                staff.save()
                staffUser = Users.objects.filter(Q(role='doctor') | Q(role='nurse')).values('user_id','name','role','username','gender','date_of_birth', 'email', 'phone_number', 'address', 'postcode')
                context={
                    'staffdetails':staffUser
                    }
                print("where want to change password and username togther")
                print(fullname,gender,address,postcode,dob,username,email,phnumber,usertype,hourtype,pwd,confpwd,mon,tue,wed,thu,fri)
                return redirect('staffDetail')

    print( monday, tuesday, wednesday, thursday, friday)

            
    
    context = {
                            'fullname': user.name,
                            'username': user.username,
                            'gender' : user.gender,
                            'dob': dates,
                            'mon':monday,
                            'tue':tuesday,
                            'wed':wednesday,
                            'thu':thursday,
                            'fri':friday,
                            'address': user.address,
                            'postcode': user.postcode,
                            'email': user.email,
                            'phnumber': user.phone_number,
                            'userTypeOptions': user.role,
                            'hourTypeOptions' : staff.hour_type,
                            'user_data': user_data,
                            'mode' : 'edit'
                        }

    print(context)
    return render(request, 'staffSignUpPage.html', context)

def extract_data_csv(request):
    # Retrieve user data from session
    user_data = request.session.get('user_data', {})  
    name = user_data.get('name')
    
    # Filter users based on roles (doctor or nurse)
    users = Users.objects.filter(role__in=['doctor', 'nurse'])

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