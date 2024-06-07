from django.core.exceptions import ObjectDoesNotExist
import re
from passlib.hash import sha256_crypt
import hashlib
from database_models.models import Users, Staffs

class Admins():
    pass

# validation function
def validate_password(password):
    print("Validating: ", password)
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    # Check if the password matches the pattern
    if re.match(pattern, password):
        print("True: ", password)
        return True
    else:
        print("False: ", password)
        return False

def validate_username(username):
    pattern = r"^[a-zA-Z0-9]{3,}$"
    if re.match(pattern, username):
        return True
    else:
        return False

def validate_phonenumber(phonenumber):
    pattern = r"^\d{11}$"
    if re.match(pattern, phonenumber):
        return True
    else:
        return False
    
def checking_username(username):
    try:
        Users.objects.get(username=username)
        return False  # Username found in Users
    except ObjectDoesNotExist:
        pass

    return True  # Username not found in any model

def hash_password(password):
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    return hashed_password