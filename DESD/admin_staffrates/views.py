from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from database_models.models import *
from DESD.views import verify_user_role

def admin_staffrate(request): 
  user_data = request.session.get('user_data', {})
  
  if not verify_user_role(user_data.get('role'), 'admin'):
    return redirect('/')
  
  staff_rates = StaffRates.objects.all()
  context = {
    'user_data': user_data,
    'rates': staff_rates,
  }
  return render(request, "staff_rates.html", context)

def edit_staff_rate(request, staff_rate_id):
  staff_rate = get_object_or_404(StaffRates, staff_rate_id=staff_rate_id) 
  if request.method == "POST":
    rate_Type = request.POST['rateType']
    Rate_per_hr = request.POST['ratePerHr']
    Wage_per_hr = request.POST['wagePerHr']
    
    staff_rate.rate_type = rate_Type
    staff_rate.rate_per_hr = Rate_per_hr
    staff_rate.wage_per_hr = Wage_per_hr
    staff_rate.save()
    messages.success(request, "Staff Rate Details have been successfully updated")
    return redirect('admin_staffrate')
  return redirect('admin_staffrate')

#def delete_staff_rate(request, staff_rate_id):
  #staff_rate = get_object_or_404(StaffRates, staff_rate_id=staff_rate_id)
  #staff_rate.delete()    
  #messages.error(request, "Staff Rate has been deleted")
  #return redirect('admin_staffrate')