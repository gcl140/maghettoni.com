import json
# settings.py (REQUIRED for safe JSON embedding)
from django.utils.safestring import mark_safe
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from yuzzaz import models
from .models import Payment
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest
from .forms import PropertyForm, UnitForm, TenantForm, PaymentForm, MaintenanceRequestForm
from django.core.paginator import Paginator

@login_required
def dashboard(request):
    # Get all properties owned by the user
    properties = Property.objects.filter(owner=request.user)
    
    # Calculate total properties
    total_properties = properties.count()
    
    # Calculate total units
    total_units = Unit.objects.filter(property__owner=request.user).count()
    
    # Calculate occupied units
    occupied_units = Unit.objects.filter(property__owner=request.user, is_occupied=True).count()
    
    # Calculate vacancy rate
    vacancy_rate = 0
    if total_units > 0:
        vacancy_rate = ((total_units - occupied_units) / total_units) * 100
    
    # Get recent payments
    recent_payments = Payment.objects.filter(
        property__owner=request.user
    ).order_by('-payment_date')[:10]
    
    # Calculate total revenue
    total_revenue = Payment.objects.filter(
        property__owner=request.user,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get pending maintenance requests
    pending_maintenance = MaintenanceRequest.objects.filter(
        property__owner=request.user,
        status='pending'
    ).count()
    revenue = (
        Payment.objects
        .filter(status="completed")
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    labels = [r["month"].strftime("%b %Y") for r in revenue]
    data = [float(r["total"]) for r in revenue]
    context = {
        'total_properties': total_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacancy_rate': round(vacancy_rate, 2),
        'total_revenue': total_revenue,
        'recent_payments': recent_payments,
        'pending_maintenance': pending_maintenance,
        'properties': properties,
        "revenue_labels": json.dumps(labels),
        "revenue_data": json.dumps(data),
    }
    
    return render(request, 'dashboardd/dashboard.html', context)

# @login_required
# def property_list(request):
#     properties = Property.objects.filter(owner=request.user)
#     context = {'properties': properties}
#     return render(request, 'properties/list.html', context)

from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Property

@login_required
def property_list(request):
    # Get properties with annotated unit counts (using units_list for Unit objects)
    properties_list = Property.objects.filter(owner=request.user)\
        .annotate(
            total_unit_objects=Count('units_list'),
            occupied_units_count=Count('units_list', filter=Q(units_list__is_occupied=True))
        )\
        .order_by('-created_at')
    
    # Pagination
    paginator = Paginator(properties_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate overall stats
    total_property_units = sum(property.units for property in page_obj.object_list)  # Integer field from Property model
    total_unit_objects = sum(property.total_unit_objects for property in page_obj.object_list)  # Count of Unit objects
    total_occupied = sum(property.occupied_units_count for property in page_obj.object_list)
    
    # Calculate occupancy rate based on Unit objects, fallback to Property units
    if total_unit_objects > 0:
        occupancy_rate = (total_occupied / total_unit_objects * 100)
    elif total_property_units > 0:
        # If no Unit objects exist yet, use a placeholder or different calculation
        occupancy_rate = 0  # Or calculate differently
    else:
        occupancy_rate = 0
    
    context = {
        'page_obj': page_obj,
        'properties': page_obj.object_list,
        'total_property_units': total_property_units,
        'total_unit_objects': total_unit_objects,
        'total_occupied': total_occupied,
        'occupancy_rate': occupancy_rate,
    }
    return render(request, 'properties/list.html', context)


@login_required
def property_delete(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('property_list')
    
    context = {
        'property': property_obj,
    }
    return redirect('property_list')
    # return render(request, 'properties/confirm_delete.html', context)

# views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # or use @csrf_protect if sending CSRF token
def location_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        lat = data.get("lat")
        lng = data.get("lng")

        # TODO: convert lat/lng to address via geocoding
        address = f"Fake address for ({lat}, {lng})"

        return JsonResponse({"address": address})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def property_edit(request, property_id=None):
    # If property_id is provided, we're editing; otherwise, we're adding
    if property_id:
        property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
        is_edit = True
        title = "Edit Property"
        success_message = "Property updated successfully!"
    else:
        property_obj = None
        is_edit = False
        title = "Add New Property"
        success_message = "Property added successfully!"
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            property_obj = form.save(commit=False)
            if not is_edit:
                property_obj.owner = request.user
            property_obj.save()
            messages.success(request, success_message)
            if is_edit:
                return redirect('property_detail', property_id=property_obj.id)
            else:
                return redirect('property_list')
    else:
        form = PropertyForm(instance=property_obj)
    
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
        'property': property_obj,
    }
    return render(request, 'properties/edit.html', context)


@login_required
def property_units(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all()
    
    context = {
        'property': property_obj,
        'units': units,
    }
    
    return render(request, 'properties/units.html', context)


@login_required
def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all()
    tenants = property_obj.tenants.all()
    
    # Calculate property statistics
    total_units = units.count()
    occupied_units = units.filter(is_occupied=True).count()
    vacancy_rate = 0
    if total_units > 0:
        vacancy_rate = ((total_units - occupied_units) / total_units) * 100
    
    # Recent payments for this property
    recent_payments = Payment.objects.filter(property=property_obj).order_by('-payment_date')[:5]
    
    # Maintenance requests
    maintenance_requests = MaintenanceRequest.objects.filter(property=property_obj).order_by('-reported_date')[:5]
    
    context = {
        'property': property_obj,
        'units': units,
        'tenants': tenants,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacancy_rate': round(vacancy_rate, 2),
        'recent_payments': recent_payments,
        'maintenance_requests': maintenance_requests,
    }
    
    return render(request, 'properties/detail.html', context)



# @login_required
# def tenant_list(request):
#     tenants = Tenant.objects.filter(property__owner=request.user)
#     return render(request, 'tenants/list.html', {'tenants': tenants})


@login_required
def tenant_list(request):
    # Get tenants belonging to properties owned by the current user
    tenants_list = Tenant.objects.filter(property__owner=request.user)\
        .select_related('property', 'unit')\
        .order_by('-move_in_date')
    
    # Get search query
    search_query = request.GET.get('search', '')
    if search_query:
        tenants_list = tenants_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(property__name__icontains=search_query)
        )
    
    # Pagination - 10 tenants per page
    paginator = Paginator(tenants_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats
    total_tenants = tenants_list.count()
    active_tenants = tenants_list.filter(status='active').count()
    pending_tenants = tenants_list.filter(status='pending').count()
    inactive_tenants = tenants_list.filter(status='inactive').count()
    
    context = {
        'page_obj': page_obj,
        'tenants': page_obj.object_list,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'pending_tenants': pending_tenants,
        'inactive_tenants': inactive_tenants,
        'search_query': search_query,
    }
    return render(request, 'tenants/list.html', context)

# @login_required
# def tenant_detail(request, tenant_id):
#     tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
#     payments = tenant.payments.all().order_by('-payment_date')
    
#     # Calculate total paid
#     total_paid = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
#     # Get upcoming payments
#     today = timezone.now().date()
#     upcoming_payments = payments.filter(due_date__gte=today, status='pending')
    
#     context = {
#         'tenant': tenant,
#         'payments': payments,
#         'total_paid': total_paid,
#         'upcoming_payments': upcoming_payments,
#     }
    
#     return render(request, 'tenants/detail.html', context)


@login_required
def tenant_activate(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    tenant.status = 'active'
    tenant.save()
    name = tenant.full_name()
    messages.success(request, f'{name} has been activated!')
    return redirect('tenant_detail', tenant_id=tenant.id)

@login_required
def tenant_deactivate(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    tenant.status = 'inactive'
    tenant.save()
    name = tenant.full_name()
    messages.success(request, f'{name} has been deactivated!')
    return redirect('tenant_detail', tenant_id=tenant.id)

@login_required
def tenant_delete(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    tenant_name = tenant.full_name()
    tenant.delete()
    messages.success(request, f'Tenant {tenant_name} has been removed!')
    return redirect('tenant_list')

@login_required
def tenant_detail(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    
    # Get related data
    payments = tenant.payments.all().order_by('-payment_date')[:5]
    maintenance_requests = tenant.maintenance_requests.all().order_by('-reported_date')[:5]
    
    # Calculate stats
    total_payments = tenant.payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_payments = tenant.payments.filter(status='pending').count()
    active_maintenance = tenant.maintenance_requests.filter(status__in=['pending', 'in_progress']).count()
    
    # Calculate tenancy duration
    today = timezone.now().date()
    days_in_tenancy = (today - tenant.move_in_date).days if tenant.move_in_date else 0
    
    context = {
        'tenant': tenant,
        'payments': payments,
        'maintenance_requests': maintenance_requests,
        'total_payments': total_payments,
        'pending_payments': pending_payments,
        'active_maintenance': active_maintenance,
        'days_in_tenancy': days_in_tenancy,
        'today': today,
    }
    return render(request, 'tenants/detail.html', context)


@login_required
def tenant_edit(request, tenant_id=None):
    """
    Combined view for adding and editing tenants
    """
    # If tenant_id is provided, we're editing; otherwise, we're adding
    if tenant_id:
        tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
        is_edit = True
        title = "Edit Tenant"
        success_message = "Tenant updated successfully! 🎉"
    else:
        tenant = None
        is_edit = False
        title = "Add New Tenant"
        success_message = "Tenant added successfully! 🎉"
    
    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES, instance=tenant, user=request.user)
        if form.is_valid():
            tenant = form.save(commit=False)
            
            # If adding new tenant, mark the unit as occupied
            if not is_edit and tenant.unit:
                tenant.unit.is_occupied = True
                tenant.unit.save()
            
            # If editing and changing unit, update occupancy status
            if is_edit and tenant.unit_id != form.initial.get('unit'):
                old_unit = Unit.objects.filter(id=form.initial.get('unit')).first()
                if old_unit:
                    old_unit.is_occupied = False
                    old_unit.save()
                if tenant.unit:
                    tenant.unit.is_occupied = True
                    tenant.unit.save()
            
            tenant.save()
            
            messages.success(request, success_message)
            if is_edit:
                return redirect('tenant_detail', tenant_id=tenant.id)
            else:
                return redirect('tenant_list')
    else:
        form = TenantForm(instance=tenant, user=request.user)
    
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
        'tenant': tenant,
    }
    return render(request, 'tenants/edit.html', context)

# Add this to views.py if you want dynamic unit filtering
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@login_required
@require_GET
def get_available_units(request, property_id):
    """API endpoint to get available units for a property"""
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    # Get all units for this property
    units = Unit.objects.filter(property=property_obj).order_by('unit_number')
    
    units_data = []
    for unit in units:
        units_data.append({
            'id': unit.id,
            'unit_number': unit.unit_number,
            'bedrooms': unit.bedrooms,
            'bathrooms': unit.bathrooms,
            'monthly_rent': str(unit.monthly_rent),
            'is_occupied': unit.is_occupied,
            'square_feet': unit.square_feet,
        })
    
    return JsonResponse({'units': units_data})

# Add to urls.py:
# path('api/properties/<int:property_id>/units/available/', views.get_available_units, name='available_units'),

@login_required
def payments_list(request):
    payments = Payment.objects.filter(property__owner=request.user).order_by('-payment_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Calculate totals
    total_completed = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': payments,
        'total_completed': total_completed,
        'total_pending': total_pending,
        'status_filter': status_filter,
    }
    
    return render(request, 'payments/list.html', context)

@login_required
def record_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Payment recorded successfully!')
            return redirect('payments_list')
    else:
        form = PaymentForm(user=request.user)
    
    return render(request, 'payments/record.html', {'form': form})

@login_required
def maintenance_requests(request):
    requests = MaintenanceRequest.objects.filter(property__owner=request.user).order_by('-reported_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
    }
    
    return render(request, 'maintenance/list.html', context)

# @login_required
# def create_maintenance_request(request):
#     if request.method == 'POST':
#         form = MaintenanceRequestForm(request.POST, user=request.user)
#         if form.is_valid():
#             maintenance_request = form.save()
#             messages.success(request, 'Maintenance request created successfully!')
#             return redirect('maintenance_requests')
#     else:
#         form = MaintenanceRequestForm(user=request.user)
    
#     return render(request, 'maintenance/create.html', {'form': form})

from datetime import timedelta


@login_required
def payments_list(request):
    # Get payments for properties owned by current user
    payments_list = Payment.objects.filter(property__owner=request.user)\
        .select_related('property', 'tenant')\
        .order_by('-payment_date')
    
    # Get search query
    search_query = request.GET.get('search', '')
    if search_query:
        payments_list = payments_list.filter(
            Q(tenant__first_name__icontains=search_query) |
            Q(tenant__last_name__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(property__name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments_list = payments_list.filter(status=status_filter)
    
    # Filter by date range
    today = timezone.now().date()
    date_filter = request.GET.get('date', '')
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            payments_list = payments_list.filter(payment_date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            payments_list = payments_list.filter(payment_date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            payments_list = payments_list.filter(payment_date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(payments_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats
    total_received = payments_list.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_amount = payments_list.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    overdue_payments = payments_list.filter(status='pending', due_date__lt=today).count()
    
    context = {
        'page_obj': page_obj,
        'payments': page_obj.object_list,
        'total_received': total_received,
        'pending_amount': pending_amount,
        'overdue_payments': overdue_payments,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'today': timezone.now().date(),
    }
    return render(request, 'payments/list.html', context)

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, property__owner=request.user)
    
    if request.method == 'POST':
        if 'mark_paid' in request.POST:
            payment.status = 'completed'
            payment.payment_date = timezone.now().date()
            payment.save()
            messages.success(request, 'Payment marked as completed!')
            return redirect('payment_detail', payment_id=payment.id)
        elif 'update_status' in request.POST:
            payment.status = request.POST.get('status')
            payment.save()
            messages.success(request, 'Payment status updated!')
            return redirect('payment_detail', payment_id=payment.id)
    
    context = {
        'payment': payment,
        'is_overdue': payment.due_date < timezone.now().date() and payment.status == 'pending',
    }
    return render(request, 'payments/detail.html', context)

# @login_required
# def payment_create(request):
#     if request.method == 'POST':
#         form = PaymentForm(request.POST, user=request.user)
#         if form.is_valid():
#             payment = form.save(commit=False)
#             payment.save()
#             messages.success(request, 'Payment record created successfully!')
#             return redirect('payments_list')
#     else:
#         form = PaymentForm(user=request.user)
    
#     context = {'form': form}
#     return render(request, 'payments/create.html', context)

@login_required
def payment_edit(request, payment_id=None):
    """
    Combined view for adding and editing payments
    """
    # If payment_id is provided, we're editing; otherwise, we're adding
    if payment_id:
        payment = get_object_or_404(Payment, id=payment_id, property__owner=request.user)
        is_edit = True
        title = "Edit Payment Record"
        success_message = "Malipo yamebadilishwa kikamilifu! 💰"
    else:
        payment = None
        is_edit = False
        title = "Record New Payment"
        success_message = "Malipo yamehifadhiwa kikamilifu! 💰"
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            
            # If marking as completed and payment_date is today's default, update to actual date
            if payment.status == 'completed' and payment.payment_date == timezone.now().date():
                payment.payment_date = timezone.now().date()
            
            payment.save()
            
            messages.success(request, success_message)
            if is_edit:
                return redirect('payment_detail', payment_id=payment.id)
            else:
                return redirect('payments_list')
    else:
        form = PaymentForm(instance=payment, user=request.user)
    
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
        'payment': payment,
    }
    return render(request, 'payments/edit.html', context)

# ========== MAINTENANCE REQUESTS ==========

@login_required
def maintenance_requests_list(request):
    # Get maintenance requests for properties owned by current user
    requests_list = MaintenanceRequest.objects.filter(property__owner=request.user)\
        .select_related('property', 'unit', 'tenant')\
        .order_by('-reported_date')
    
    # Get search query
    search_query = request.GET.get('search', '')
    if search_query:
        requests_list = requests_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tenant__first_name__icontains=search_query) |
            Q(tenant__last_name__icontains=search_query) |
            Q(property__name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    
    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        requests_list = requests_list.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(requests_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats
    total_requests = requests_list.count()
    open_requests = requests_list.filter(status__in=['pending', 'in_progress']).count()
    emergency_requests = requests_list.filter(priority='emergency', status__in=['pending', 'in_progress']).count()
    total_cost = requests_list.filter(status='completed').aggregate(Sum('cost'))['cost__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'requests': page_obj.object_list,
        'total_requests': total_requests,
        'open_requests': open_requests,
        'emergency_requests': emergency_requests,
        'total_cost': total_cost,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    }
    return render(request, 'maintenance/list.html', context)

@login_required
def maintenance_request_detail(request, request_id):
    maintenance_request = get_object_or_404(
        MaintenanceRequest, id=request_id, property__owner=request.user
    )
    
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, instance=maintenance_request, user=request.user)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            if maintenance_request.status == 'completed' and not maintenance_request.completed_date:
                maintenance_request.completed_date = timezone.now()
            maintenance_request.save()
            messages.success(request, 'Maintenance request updated!')
            return redirect('maintenance_request_detail', request_id=maintenance_request.id)
    else:
        form = MaintenanceRequestForm(instance=maintenance_request, user=request.user)
    
    context = {
        'request': maintenance_request,
        'form': form,
    }
    return render(request, 'maintenance/detail.html', context)


@login_required
def maintenance_request_edit(request, request_id=None):
    """
    Combined view for adding and editing maintenance requests
    """
    # If request_id is provided, we're editing; otherwise, we're adding
    if request_id:
        maintenance_request = get_object_or_404(
            MaintenanceRequest, id=request_id, property__owner=request.user
        )
        is_edit = True
        title = "Edit Maintenance Request"
        success_message = "Maintenance request updated successfully! 🛠️"
    else:
        maintenance_request = None
        is_edit = False
        title = "Create Maintenance Request"
        success_message = "Maintenance request created successfully! 🛠️"
    
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, instance=maintenance_request, user=request.user)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            
            # If marking as completed, set the completed date
            if maintenance_request.status == 'completed' and not maintenance_request.completed_date:
                maintenance_request.completed_date = timezone.now()
            
            maintenance_request.save()
            
            messages.success(request, success_message)
            if is_edit:
                return redirect('maintenance_request_detail', request_id=maintenance_request.id)
            else:
                return redirect('maintenance_requests_list')
    else:
        form = MaintenanceRequestForm(instance=maintenance_request, user=request.user)
    
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
        'maintenance_request': maintenance_request,
    }
    return render(request, 'maintenance/edit.html', context)

def about(request):
    context = {        
    }
    return render(request, 'dashboardd/about.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import UnitForm
from .models import Property, Unit

@login_required
def property_units(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all()
    
    # Calculate statistics
    total_units = units.count()
    occupied_units = units.filter(is_occupied=True).count()
    vacant_units = total_units - occupied_units
    total_monthly_rent = units.aggregate(Sum('monthly_rent'))['monthly_rent__sum'] or 0
    
    context = {
        'property': property_obj,
        'units': units,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'total_monthly_rent': total_monthly_rent,
    }
    
    return render(request, 'properties/units.html', context)

@login_required
def unit_edit(request, property_id, unit_id=None):
    """
    Combined view for adding and editing units
    """
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    # If unit_id is provided, we're editing; otherwise, we're adding
    if unit_id:
        unit = get_object_or_404(Unit, id=unit_id, property=property_obj)
        is_edit = True
        title = "Edit Unit"
        success_message = f"Unit {unit.unit_number} updated successfully! 🎉"
    else:
        unit = None
        is_edit = False
        title = "Add New Unit"
        success_message = "New unit added successfully! 🎉"
    
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.property = property_obj  # Always set the property
            
            # Check for duplicate unit number
            duplicate_units = Unit.objects.filter(
                property=property_obj, 
                unit_number=unit.unit_number
            )
            if unit.pk:
                duplicate_units = duplicate_units.exclude(pk=unit.pk)
            
            if duplicate_units.exists():
                messages.error(request, f"Unit number {unit.unit_number} already exists in this property!")
            else:
                unit.save()
                messages.success(request, success_message)
                return redirect('property_units', property_id=property_obj.id)
    else:
        form = UnitForm(instance=unit)
    
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
        'property': property_obj,
        'unit': unit,
    }
    return render(request, 'properties/unit_edit.html', context)

@login_required
def unit_delete(request, property_id, unit_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    unit = get_object_or_404(Unit, id=unit_id, property=property_obj)
    
    if request.method == 'POST':
        unit_number = unit.unit_number
        unit.delete()
        messages.success(request, f"Unit {unit_number} deleted successfully!")
        return redirect('property_units', property_id=property_obj.id)
    
    return redirect('property_units', property_id=property_obj.id)

# Add this to views.py if you want dynamic unit/tenant filtering
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@login_required
@require_GET
def get_property_units_tenants(request, property_id):
    """API endpoint to get units and tenants for a property"""
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    # Get all units for this property
    units = Unit.objects.filter(property=property_obj).order_by('unit_number')
    units_data = []
    for unit in units:
        units_data.append({
            'id': unit.id,
            'unit_number': unit.unit_number,
            'bedrooms': unit.bedrooms,
            'bathrooms': unit.bathrooms,
            'is_occupied': unit.is_occupied,
        })
    
    # Get all tenants for this property
    tenants = Tenant.objects.filter(property=property_obj).order_by('first_name')
    tenants_data = []
    for tenant in tenants:
        tenants_data.append({
            'id': tenant.id,
            'first_name': tenant.first_name,
            'last_name': tenant.last_name,
            'unit_number': tenant.unit.unit_number if tenant.unit else 'N/A',
        })
    
    return JsonResponse({
        'units': units_data,
        'tenants': tenants_data,
    })

# Add to urls.py:
# path('api/properties/<int:property_id>/units-tenants/', views.get_property_units_tenants, name='property_units_tenants'),

# Add this to views.py for dynamic tenant info
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@login_required
@require_GET
def get_tenant_details(request, tenant_id):
    """API endpoint to get tenant details including unit info"""
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    
    data = {
        'id': tenant.id,
        'full_name': tenant.full_name(),
        'property_id': tenant.property.id,
        'property_name': tenant.property.name,
        'unit': None,
    }
    
    if tenant.unit:
        data['unit'] = {
            'id': tenant.unit.id,
            'unit_number': tenant.unit.unit_number,
            'bedrooms': tenant.unit.bedrooms,
            'bathrooms': tenant.unit.bathrooms,
            'monthly_rent': str(tenant.unit.monthly_rent),
        }
    
    return JsonResponse(data)

# Add to urls.py:
# path('api/tenants/<int:tenant_id>/details/', views.get_tenant_details, name='tenant_details'),