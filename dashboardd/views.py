from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest
from .forms import PropertyForm, UnitForm, TenantForm, PaymentForm, MaintenanceRequestForm

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
    
    context = {
        'total_properties': total_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacancy_rate': round(vacancy_rate, 2),
        'total_revenue': total_revenue,
        'recent_payments': recent_payments,
        'pending_maintenance': pending_maintenance,
        'properties': properties,
    }
    
    return render(request, 'dashboardd/dashboard.html', context)

@login_required
def property_list(request):
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'dashboardd/properties/list.html', {'properties': properties})

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

@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            messages.success(request, 'Property added successfully!')
            return redirect('property_list')
    else:
        form = PropertyForm()
    
    return render(request, 'properties/add.html', {'form': form})

@login_required
def tenant_list(request):
    tenants = Tenant.objects.filter(property__owner=request.user)
    return render(request, 'tenants/list.html', {'tenants': tenants})

@login_required
def tenant_detail(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    payments = tenant.payments.all().order_by('-payment_date')
    
    # Calculate total paid
    total_paid = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
    # Get upcoming payments
    today = timezone.now().date()
    upcoming_payments = payments.filter(due_date__gte=today, status='pending')
    
    context = {
        'tenant': tenant,
        'payments': payments,
        'total_paid': total_paid,
        'upcoming_payments': upcoming_payments,
    }
    
    return render(request, 'tenants/detail.html', context)

@login_required
def add_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST, user=request.user)
        if form.is_valid():
            tenant = form.save()
            
            # Update unit occupancy
            if tenant.unit:
                tenant.unit.is_occupied = True
                tenant.unit.save()
            
            messages.success(request, 'Tenant added successfully!')
            return redirect('tenant_detail', tenant_id=tenant.id)
    else:
        form = TenantForm(user=request.user)
    
    return render(request, 'tenants/add.html', {'form': form})

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

@login_required
def create_maintenance_request(request):
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            maintenance_request = form.save()
            messages.success(request, 'Maintenance request created successfully!')
            return redirect('maintenance_requests')
    else:
        form = MaintenanceRequestForm(user=request.user)
    
    return render(request, 'maintenance/create.html', {'form': form})