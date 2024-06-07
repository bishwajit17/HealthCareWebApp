from django.db import models
from datetime import date

ROLES = (
    ('doctor', 'Doctor'),
    ('nurse', 'Nurse'),
    ('patient', 'Patient'),
    ('admin', 'Admin'),
    ('deleted_user', 'Deleted_User')
)

GENDER = (
    ('m', 'M'),
    ('f', 'F'),
)

HOUR_TYPE = (
    ('full', 'Full-time'),
    ('part', 'Part-time')
)
APPOINTMENT_STATUS = (
    ('completed', 'Completed'),
    ('upcoming', 'Upcoming'),
    ('on-going', 'On-going'),
    ('cancelled', 'Cancelled')
)

APPOINTMENT_OUTCOME = (
    ('prescribed', 'Prescribed'),
    ('forwarded', 'Forwarded'),
    ('awaiting', 'Awaiting'),
    ('cancelled', 'Cancelled')
)

PAYMENT_SOURCE = (
    ('private', 'Private'),
    ('nhs', 'NHS')
)

PRESCRIPTION_TYPE = (
    ('liquid', 'Liquid'),
    ('tablet', 'Tablet'),
    ('capsules', 'Capsules'),
    ('drops', 'Drops'),
    ('inhalers', 'Inhalers'),
    ('other', 'Other')
)

PRESCRIPTION_STATUS = (
    ('requested','Requested'),
    ('approved', 'Approved'),
    ('collected', 'Collected'),
    ('request denied', 'Request Denied')
)

COLLECTION_STATUS = (
    ('awaiting decision', 'Awaiting Decision'),
    ('waiting to collect', 'Waiting To Collect'),
    ('collected', 'Collected'),
    ('cancelled', 'Cancelled')
)

INDIVIDUAL_TYPES = (
    ('doctor/nurse', 'Doctor/Nurse'),
    ('doctor', 'Doctor'),
    ('nurse', 'Nurse'),
    ('patient', 'Patient'),
    ('admin', 'admin'),
    ('all', 'All')
)

RATE_TYPE = (
    ('doctor', 'Doctor'),
    ('nurse', 'Nurse')
)

APPOINTMENT_CANCELLATION_TYPES = (
    ('sick leave', 'Sick Leave'),
    ('on holiday', 'On Holiday'),
    ('emergency', 'Emergency'),
    ('deleted user', 'Deleted User'),
    ('incorrect prescription', 'Incorrect Prescription'),
    ('outdated prescription', 'Outdated Prescription'),
    ('prescription cancelled (doctor/nurse)', 'Prescription Cancelled (Doctor/Nurse)'),
    ('prescription cancelled (patient)','Prescription Cancelled (Patient)'),
    ('appointment cancelled (doctor/nurse)', 'Appointment Cancelled (Doctor/Nurse)'),
    ('appointment cancelled (patient)', 'Appointment Cancelled (Patient)')
)

DAYS = (
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
)

class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, default='default')
    role = models.CharField(max_length=50, choices=ROLES, default='default')
    username = models.CharField(max_length=50, default='default')
    password = models.CharField(max_length=100, default='default')
    gender = models.CharField(max_length=10, choices=GENDER, default='M', null=True)
    date_of_birth = models.DateField(default=date.today, null=True)
    email = models.CharField(max_length=200, default='default', null=True)
    phone_number = models.CharField(max_length=20, default='123456789', null=True)
    address = models.CharField(max_length=200, default='default', null=True)
    postcode = models.CharField(max_length=15, default='default', null=True)
    is_active = models.BooleanField(default=1)

class StaffRates(models.Model):
    staff_rate_id = models.AutoField(primary_key=True)
    rate_type = models.CharField(max_length=50, choices=RATE_TYPE, default='doctor')
    rate_per_hr = models.DecimalField(max_digits=8, decimal_places=2)
    wage_per_hr = models.DecimalField(max_digits=8, decimal_places=2, default=0)

class Staffs(models.Model):
    staff_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, default='1')
    staff_rate = models.ForeignKey(StaffRates, on_delete=models.CASCADE)
    hour_type = models.CharField(max_length=50, choices=HOUR_TYPE, default='full')
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()

class Days(models.Model):
    day_id = models.AutoField(primary_key=True)
    day = models.CharField(max_length=12, choices=DAYS, default='monday')

class Durations(models.Model):
    duration_id = models.AutoField(primary_key=True)
    duration_length = models.IntegerField(default=1)

class Schedules(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    day = models.ForeignKey(Days, on_delete=models.CASCADE)
    role = models.CharField(max_length=12, choices=RATE_TYPE, default='monday')

class Slots(models.Model):
    slot_id = models.AutoField(primary_key=True)
    schedule = models.ForeignKey(Schedules, on_delete=models.CASCADE)
    duration = models.ForeignKey(Durations, on_delete=models.CASCADE)
    start_time = models.TimeField()

class Patients(models.Model):
    patient_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, default='1')
    payment_source = models.CharField(max_length=50, choices=PAYMENT_SOURCE, default='private')

class Appointments(models.Model):
    appointment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staffs, on_delete=models.CASCADE, default=1)
    appointment_date = models.DateField(default=date.today)
    appointment_start = models.TimeField()
    appointment_end = models.TimeField()
    consultation_cost = models.DecimalField(max_digits=8, decimal_places=2)
    appointment_status = models.CharField(max_length=50, choices=APPOINTMENT_STATUS, default='upcoming')
    appointment_outcome = models.CharField(max_length=50, choices=APPOINTMENT_OUTCOME, default='complete')
    appointment_payment_status = models.BooleanField()

class Prescriptions(models.Model):
    prescription_id = models.AutoField(primary_key=True)
    prescription_name = models.CharField(max_length=150, default='default')
    prescription_type = models.CharField(max_length=50, choices=PRESCRIPTION_TYPE, default='liquid')

class PrescriptionsAssignments(models.Model):
    prescription_assignment_id = models.AutoField(primary_key=True)
    prescription = models.ForeignKey(Prescriptions, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointments, on_delete=models.CASCADE)
    prescription_cost = models.DecimalField(max_digits=8, decimal_places=2)
    prescription_status = models.CharField(max_length=50, choices=PRESCRIPTION_STATUS, default='requested')
    issued_date = models.DateField(default=date.today, null=True)
    quantity = models.IntegerField()
    collection_status = models.CharField(max_length=50, choices=COLLECTION_STATUS, default='collected')
    prescription_payment_status = models.IntegerField(default=0)

class CancellationTypes(models.Model):
    cancellation_type_id = models.AutoField(primary_key=True)
    cancellation_type = models.CharField(max_length=50, choices=APPOINTMENT_CANCELLATION_TYPES, default='appointment cancelled (doctor/nurse)')
    individual_type = models.CharField(max_length=50, choices=INDIVIDUAL_TYPES, default='doctor/nurse')

class AppointmentCancellations(models.Model):
    appointment_canellation_id = models.AutoField(primary_key=True)
    cancellation_type = models.ForeignKey(CancellationTypes, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointments, on_delete=models.CASCADE)
    description = models.CharField(max_length=250, default='default')

class PrescriptionCancellations(models.Model):
    prescription_cancellation_id = models.AutoField(primary_key=True)
    prescription_assignment = models.ForeignKey(PrescriptionsAssignments, on_delete=models.CASCADE, default=1)
    cancellation_type = models.ForeignKey(CancellationTypes, on_delete=models.CASCADE)
    description = models.CharField(max_length=250, default='default')
    staff_id = models.IntegerField(default=1)

class LoginAttempts(models.Model):
    login_attempt_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, default='default')
    datetime = models.DateTimeField()