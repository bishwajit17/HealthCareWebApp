from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import re
from passlib.hash import sha256_crypt
import hashlib
from django.contrib import messages
from database_models.models import Users, Patients
from datetime import date, datetime
from django.template import loader
from .validations import *

# def signup(request):
#     return render(request, 'signupPage.html')

class Admins():
    pass


def user_signup(request):
    print("testing", request.method)

    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        dob = request.POST.get('dob')
        phnumber = request.POST.get('telnum')
        email = request.POST.get('email')
        username = request.POST.get('username')
        pwd = request.POST.get('password')
        confpwd = request.POST.get('passwordConfirm')
        payment = request.POST.get('options')


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
                            'address': address,
                            'postcode': postcode,
                            'email': email,
                            'phnumber': phnumber,
                            'payment': payment,
                            'errors': errors,
                        }
            # messages.error(request, context)
            return render(request, 'signupPage.html', context)
            # return redirect('/signup_page',context)
        else:
            hashed_pwd = hash_password(pwd)  # Hash the password
            user = Users(
                name=fullname,
                role='patient',
                gender='m',
                username=username,
                password=hashed_pwd,
                date_of_birth=dob,
                address=address,
                postcode=postcode,
                phone_number=phnumber,
                email=email,
            )
            
            user.save()

            new_user = Users.objects.get(username=username)

            patient = Patients(
                user_id=new_user.user_id,
                payment_source=payment,
            )

            patient.save()

            return redirect('/?confirmation=true')

    print("here 1")
    # template = loader.get_template("signupPage.html")
    # return HttpResponse(template.render(context, request))
    return render(request, 'signupPage.html')


