import json
import csv
import io
from datetime import timedelta
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest
from .forms import (
    PropertyForm,
    UnitForm,
    TenantForm,
    PaymentForm,
    MaintenanceRequestForm,
    MaintenanceStatusUpdateForm,
)


def _build_pdf(title, headers, rows):
    """Build a landscape A4 PDF table and return a BytesIO buffer."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    BROWN = colors.HexColor('#5c3317')
    LIGHT = colors.HexColor('#fdf8f3')

    title_style = ParagraphStyle('t', parent=styles['Heading1'], fontSize=16,
                                  textColor=BROWN, spaceAfter=12)
    cell_style  = ParagraphStyle('c', parent=styles['Normal'], fontSize=8)
    head_style  = ParagraphStyle('h', parent=styles['Normal'], fontSize=8,
                                  textColor=colors.white, fontName='Helvetica-Bold')

    col_count = len(headers)
    col_w = (landscape(A4)[0] - 3*cm) / col_count

    table_data = [[Paragraph(h, head_style) for h in headers]]
    for r in rows:
        table_data.append([Paragraph(str(c), cell_style) for c in r])

    tbl = Table(table_data, colWidths=[col_w]*col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BROWN),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#e8cba8')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))

    doc.build([Paragraph(title, title_style), Spacer(1, 0.3*cm), tbl])
    buf.seek(0)
    return buf


@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Properties Statistics
    properties = Property.objects.filter(owner=user)
    total_properties = properties.count()
    
    # Units Statistics
    units = Unit.objects.filter(property__owner=user)
    total_units = units.count()
    occupied_units = units.filter(is_occupied=True).count()
    vacant_units = total_units - occupied_units
    
    # Tenants Statistics
    tenants = Tenant.objects.filter(property__owner=user)
    total_tenants = tenants.count()
    active_tenants = tenants.filter(status='active').count()
    
    # Payments Statistics
    payments = Payment.objects.filter(property__owner=user)
    total_revenue = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent revenue (last 30 days)
    recent_revenue = payments.filter(
        status='completed',
        payment_date__gte=last_30_days
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending payments
    pending_payments = payments.filter(status='pending').count()
    pending_amount = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    
    # Overdue payments (due date passed but still pending)
    overdue_payments = payments.filter(
        status='pending',
        due_date__lt=today
    ).count()
    
    # Maintenance Statistics
    maintenance_requests = MaintenanceRequest.objects.filter(property__owner=user)
    pending_maintenance = maintenance_requests.filter(status='pending').count()
    emergency_maintenance = maintenance_requests.filter(priority='emergency', status__in=['pending', 'in_progress']).count()
    
    # Calculate vacancy rate
    vacancy_rate = 0
    if total_units > 0:
        vacancy_rate = round((vacant_units / total_units) * 100, 1)
    
    # Calculate occupancy rate
    occupancy_rate = 0
    if total_units > 0:
        occupancy_rate = round((occupied_units / total_units) * 100, 1)
    
    # Recent payments for table
    recent_payments_list = payments.filter(status='completed').order_by('-payment_date')[:5]
    
    # Recent maintenance requests
    recent_maintenance = maintenance_requests.filter(status__in=['pending', 'in_progress']).order_by('-reported_date')[:5]
    
    # New tenants this month
    new_tenants_this_month = tenants.filter(
        move_in_date__year=today.year,
        move_in_date__month=today.month
    ).count()
    
    # Revenue by month for chart
    revenue_data = (
        payments.filter(status='completed')
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')[:12]  # Last 12 months
    )
    
    # Prepare chart data
    revenue_labels = [r['month'].strftime("%b %Y") for r in revenue_data]
    revenue_values = [float(r['total']) for r in revenue_data]
    
    # Calculate revenue growth
    revenue_growth = 0
    if len(revenue_values) >= 2:
        current_month = revenue_values[-1] if revenue_values else 0
        previous_month = revenue_values[-2] if len(revenue_values) >= 2 else 0
        if previous_month > 0:
            revenue_growth = round(((current_month - previous_month) / previous_month) * 100, 1)
    
    # Payment methods distribution
    payment_methods = payments.filter(status='completed').values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Properties with highest revenue
    top_properties = properties.annotate(
        total_revenue=Sum('payments__amount', filter=Q(payments__status='completed')),
        tenant_count=Count('tenants', filter=Q(tenants__status='active'))
    ).order_by('-total_revenue')[:3]
    
    # Properties needing attention (high vacancy or pending maintenance)
    properties_needing_attention = properties.filter(
        Q(units_list__is_occupied=False) | 
        Q(maintenance_requests__status='pending')
    ).distinct()[:3]
    
    # Upcoming payments (due in next 7 days)
    upcoming_payments = payments.filter(
        status='pending',
        due_date__range=[today, today + timedelta(days=7)]
    ).order_by('due_date')[:5]
    
    # Prepare context
    context = {
        # Dashboard cards data
        'total_properties': total_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'total_revenue': total_revenue,
        'recent_revenue': recent_revenue,
        'pending_payments': pending_payments,
        'pending_amount': pending_amount,
        'overdue_payments': overdue_payments,
        'pending_maintenance': pending_maintenance,
        'emergency_maintenance': emergency_maintenance,
        'vacancy_rate': vacancy_rate,
        'occupancy_rate': occupancy_rate,
        'new_tenants_this_month': new_tenants_this_month,
        'revenue_growth': revenue_growth,
        
        # Lists for tables
        'properties': properties[:6],  # Limit to 6 for dashboard
        'recent_payments': recent_payments_list,
        'recent_maintenance': recent_maintenance,
        'upcoming_payments': upcoming_payments,
        
        # Charts data
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_data': json.dumps(revenue_values),
        
        # Additional insights
        'payment_methods': payment_methods,
        'top_properties': top_properties,
        'properties_needing_attention': properties_needing_attention,
        
        # Today's date for display
        'today': today.strftime("%B %d, %Y"),
    }
    
    return render(request, 'dashboardd/dashboard.html', context)


@login_required
def search_results(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return redirect('dashboard')

    user = request.user

    properties = Property.objects.filter(
        Q(owner=user),
        Q(name__icontains=query) |
        Q(address__icontains=query) |
        Q(property_type__icontains=query)
    ).distinct()[:20]

    tenants = Tenant.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(phone__icontains=query),
        property__owner=user
    ).distinct()[:20]

    payments = Payment.objects.filter(
        Q(tenant__first_name__icontains=query) |
        Q(tenant__last_name__icontains=query) |
        Q(reference_number__icontains=query) |
        Q(payment_method__icontains=query) |
        Q(status__icontains=query) |
        Q(notes__icontains=query),
        property__owner=user
    ).distinct()[:20]

    maintenance_requests = MaintenanceRequest.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(priority__icontains=query) |
        Q(status__icontains=query) |
        Q(unit__unit_number__icontains=query),
        property__owner=user
    ).distinct()[:20]

    units = Unit.objects.filter(
        Q(unit_number__icontains=query) |
        Q(description__icontains=query),
        property__owner=user
    ).distinct()[:20]

    special_results = {
        'total_properties': properties.count(),
        'total_tenants': tenants.count(),
        'total_payments': payments.count(),
        'total_maintenance': maintenance_requests.count(),
        'total_units': units.count(),
    }

    context = {
        'query': query,
        'properties': properties,
        'tenants': tenants,
        'payments': payments,
        'maintenance_requests': maintenance_requests,
        'units': units,
        'total_results': sum(special_results.values()),
        'special_results': special_results,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        suggestions = []

        for prop in properties[:5]:
            suggestions.append({
                'type': 'property',
                'title': prop.name,
                'subtitle': prop.address,
                'icon': 'home',
                'url': reverse('property_detail', args=[prop.id]),
                'color': 'bg-brown-100 text-brown-800'
            })

        for tenant in tenants[:5]:
            suggestions.append({
                'type': 'tenant',
                'title': tenant.full_name(),
                'subtitle': f"{tenant.property.name} - {tenant.unit.unit_number if tenant.unit else 'No Unit'}",
                'icon': 'user',
                'url': '#',
                'color': 'bg-blue-100 text-blue-800'
            })

        return JsonResponse({'suggestions': suggestions})

    return render(request, 'dashboardd/search_results.html', context)


@login_required
def quick_search(request):
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    user = request.user
    results = []

    properties = Property.objects.filter(
        name__icontains=query,
        owner=user
    )[:3]

    for prop in properties:
        results.append({
            'type': 'Mali',
            'name': prop.name,
            'detail': prop.address,
            'url': reverse('property_detail', args=[prop.id]),
            'icon': 'home'
        })

    tenants = Tenant.objects.filter(
        Q(first_name__icontains=query) |
        Q(email__icontains=query) |
        Q(last_name__icontains=query),
        property__owner=user
    )[:3]

    for tenant in tenants:
        results.append({
            'type': 'Mpangaji',
            'name': tenant.full_name(),
            'detail': tenant.phone,
            # 'url': '#',
            'url': reverse('tenant_detail', args=[tenant.id]),
            'icon': 'user'
        })

    payments = Payment.objects.filter(
        Q(reference_number__icontains=query) |
        Q(tenant__first_name__icontains=query) |
        Q(tenant__last_name__icontains=query),
        property__owner=user
    )[:3]

    for payment in payments:
        results.append({
            'type': 'Malipo',
            'name': f"TZS {payment.amount}",
            'detail': payment.tenant.full_name(),
            # 'url': '#',
            'url': reverse('payment_detail', args=[payment.id]),
            'icon': 'money-bill'
        })

    return JsonResponse({'results': results})


@login_required
def property_list(request):
    # Get properties with annotated unit counts (using units_list for Unit objects)
    properties_list = Property.objects.filter(owner=request.user)\
        .annotate(
            total_unit_objects=Count('units_list'),
            occupied_units_count=Count('units_list', filter=Q(units_list__is_occupied=True))
        )\
        .order_by('-created_at')

    search_query = request.GET.get('search', '')
    if search_query:
        properties_list = properties_list.filter(
            Q(name__icontains=search_query) | Q(address__icontains=search_query)
        )

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
        'search_query': search_query,
    }
    return render(request, 'properties/list.html', context)


@login_required
def property_delete(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('property_list')

    return render(request, 'properties/detail.html', {
        'property': property_obj,
        'units': property_obj.units_list.all(),
        'tenants': property_obj.tenants.all(),
        'total_units': property_obj.units_list.count(),
        'occupied_units': property_obj.units_list.filter(is_occupied=True).count(),
        'vacancy_rate': 0,
        'recent_payments': [],
        'maintenance_requests': [],
    })

# views.py
@login_required
@csrf_exempt
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

@login_required
def tenants_export_csv(request):
    qs = Tenant.objects.filter(property__owner=request.user)\
        .select_related('property', 'unit').order_by('-move_in_date')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="wapangaji.csv"'
    writer = csv.writer(response)
    writer.writerow(['Jina Kamili', 'Barua Pepe', 'Simu', 'Mali', 'Chumba', 'Hali', 'Tarehe ya Kuingia', 'Tarehe ya Kutoka'])
    for t in qs:
        writer.writerow([
            t.full_name() if hasattr(t, 'full_name') else f'{t.first_name} {t.last_name}',
            t.email or '',
            t.phone or '',
            t.property.name if t.property else '',
            t.unit.unit_number if t.unit else '',
            t.get_status_display(),
            t.move_in_date or '',
            t.move_out_date or '',
        ])
    return response

@login_required
def tenants_export_pdf(request):
    qs = Tenant.objects.filter(property__owner=request.user)\
        .select_related('property', 'unit').order_by('-move_in_date')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    headers = ['Jina Kamili', 'Barua Pepe', 'Simu', 'Mali', 'Chumba', 'Hali', 'Tarehe ya Kuingia']
    rows = []
    for t in qs:
        rows.append([
            t.full_name() if hasattr(t, 'full_name') else f'{t.first_name} {t.last_name}',
            t.email or '',
            t.phone or '',
            t.property.name if t.property else '',
            t.unit.unit_number if t.unit else '',
            t.get_status_display(),
            str(t.move_in_date) if t.move_in_date else '',
        ])

    buf = _build_pdf('Wapangaji', headers, rows)
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="wapangaji.pdf"'})

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
def payments_export_csv(request):
    qs = Payment.objects.filter(property__owner=request.user)\
        .select_related('property', 'tenant').order_by('-payment_date')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(tenant__first_name__icontains=search) |
            Q(tenant__last_name__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(property__name__icontains=search)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="malipo.csv"'
    writer = csv.writer(response)
    writer.writerow(['Mpangaji', 'Mali', 'Kiasi (TZS)', 'Tarehe ya Malipo', 'Tarehe ya Mwisho', 'Hali', 'Nambari ya Kumbukumbu'])
    for p in qs:
        writer.writerow([
            p.tenant.full_name() if hasattr(p.tenant, 'full_name') else str(p.tenant),
            p.property.name,
            p.amount,
            p.payment_date or '',
            p.due_date or '',
            p.get_status_display(),
            p.reference_number or '',
        ])
    return response

@login_required
def payments_export_pdf(request):
    qs = Payment.objects.filter(property__owner=request.user)\
        .select_related('property', 'tenant').order_by('-payment_date')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(tenant__first_name__icontains=search) |
            Q(tenant__last_name__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(property__name__icontains=search)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    headers = ['Mpangaji', 'Mali', 'Kiasi (TZS)', 'Tarehe ya Malipo', 'Tarehe ya Mwisho', 'Hali', 'Kumbukumbu']
    rows = []
    for p in qs:
        rows.append([
            p.tenant.full_name() if hasattr(p.tenant, 'full_name') else str(p.tenant),
            p.property.name,
            f'{p.amount:,.0f}',
            str(p.payment_date) if p.payment_date else '',
            str(p.due_date) if p.due_date else '',
            p.get_status_display(),
            p.reference_number or '',
        ])

    buf = _build_pdf('Malipo', headers, rows)
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="malipo.pdf"'})

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
        elif 'status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in ['pending', 'completed', 'failed', 'refunded']:
                payment.status = new_status
                payment.save()
                messages.success(request, f'Status updated to {payment.get_status_display()}.')
            return redirect('payment_detail', payment_id=payment.id)

    context = {
        'payment': payment,
        'is_overdue': payment.due_date and payment.due_date < timezone.now().date() and payment.status == 'pending',
    }
    return render(request, 'payments/detail.html', context)

@login_required
def payment_receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, property__owner=request.user)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    BROWN = colors.HexColor('#5c3317')
    LIGHT = colors.HexColor('#fdf8f3')

    title_style = ParagraphStyle('title', parent=styles['Heading1'], fontSize=20,
                                  textColor=BROWN, spaceAfter=4)
    sub_style   = ParagraphStyle('sub',   parent=styles['Normal'],  fontSize=9,
                                  textColor=colors.grey, spaceAfter=20)
    label_style = ParagraphStyle('label', parent=styles['Normal'],  fontSize=8,
                                  textColor=colors.grey)
    value_style = ParagraphStyle('value', parent=styles['Normal'],  fontSize=10,
                                  textColor=colors.HexColor('#1f2937'))
    amount_style= ParagraphStyle('amount',parent=styles['Heading1'],fontSize=28,
                                  textColor=colors.HexColor('#16a34a'), alignment=TA_CENTER)

    status_color = {'completed': '#16a34a', 'pending': '#d97706',
                    'failed': '#dc2626', 'refunded': '#6b7280'}
    sc = colors.HexColor(status_color.get(payment.status, '#6b7280'))

    def row(label, value):
        return [Paragraph(label, label_style), Paragraph(str(value), value_style)]

    details = Table([
        row('Reference',      payment.reference_number or '—'),
        row('Tenant',         payment.tenant.full_name() if hasattr(payment.tenant, 'full_name') else str(payment.tenant)),
        row('Property',       payment.property.name),
        row('Unit',           payment.tenant.unit.unit_number if payment.tenant.unit else '—'),
        row('Payment Date',   payment.payment_date.strftime('%d %B %Y') if payment.payment_date else '—'),
        row('Due Date',       payment.due_date.strftime('%d %B %Y') if payment.due_date else '—'),
        row('Method',         payment.get_payment_method_display()),
        row('Status',         payment.get_status_display()),
    ], colWidths=[5*cm, 11*cm])
    details.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, LIGHT]),
        ('TOPPADDING',  (0,0), (-1,-1), 7),
        ('BOTTOMPADDING',(0,0),(-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#e8cba8')),
        ('TEXTCOLOR', (0, 6), (1, 6), sc),  # status row coloured
    ]))

    from datetime import date as _date
    story = [
        Paragraph('Maghettoni', title_style),
        Paragraph(f'Payment Receipt · Issued {_date.today().strftime("%d %B %Y")}', sub_style),
        Paragraph(f'TZS {payment.amount:,.0f}', amount_style),
        Spacer(1, 0.5*cm),
        details,
        Spacer(1, 1*cm),
        Paragraph('Thank you for your payment.', ParagraphStyle('thanks', parent=styles['Normal'],
                   fontSize=9, textColor=colors.grey, alignment=TA_CENTER)),
    ]
    doc.build(story)
    buf.seek(0)
    fname = f'receipt_{payment.reference_number or payment.id}.pdf'
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename="{fname}"'})

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
def maintenance_export_csv(request):
    qs = MaintenanceRequest.objects.filter(property__owner=request.user)\
        .select_related('property', 'unit', 'tenant').order_by('-reported_date')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(property__name__icontains=search)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="matengenezo.csv"'
    writer = csv.writer(response)
    writer.writerow(['Kichwa', 'Mali', 'Chumba', 'Mpangaji', 'Kipaumbele', 'Hali', 'Tarehe', 'Gharama (TZS)'])
    for r in qs:
        writer.writerow([
            r.title,
            r.property.name if r.property else '',
            r.unit.unit_number if r.unit else '',
            r.tenant.full_name() if r.tenant and hasattr(r.tenant, 'full_name') else (str(r.tenant) if r.tenant else ''),
            r.get_priority_display(),
            r.get_status_display(),
            r.reported_date or '',
            r.cost or 0,
        ])
    return response

@login_required
def maintenance_export_pdf(request):
    qs = MaintenanceRequest.objects.filter(property__owner=request.user)\
        .select_related('property', 'unit', 'tenant').order_by('-reported_date')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(property__name__icontains=search)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    headers = ['Kichwa', 'Mali', 'Chumba', 'Mpangaji', 'Kipaumbele', 'Hali', 'Tarehe', 'Gharama (TZS)']
    rows = []
    for r in qs:
        rows.append([
            r.title,
            r.property.name if r.property else '',
            r.unit.unit_number if r.unit else '',
            r.tenant.full_name() if r.tenant and hasattr(r.tenant, 'full_name') else (str(r.tenant) if r.tenant else ''),
            r.get_priority_display(),
            r.get_status_display(),
            str(r.reported_date) if r.reported_date else '',
            f'{r.cost:,.0f}' if r.cost else '0',
        ])

    buf = _build_pdf('Matengenezo', headers, rows)
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="matengenezo.pdf"'})

@login_required
def maintenance_request_detail(request, request_id):
    maintenance_request = get_object_or_404(
        MaintenanceRequest, id=request_id, property__owner=request.user
    )
    
    if request.method == 'POST':
        form = MaintenanceStatusUpdateForm(request.POST, instance=maintenance_request)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            if maintenance_request.status == 'completed' and not maintenance_request.completed_date:
                maintenance_request.completed_date = timezone.now()
            maintenance_request.save()
            messages.success(request, 'Maintenance request updated!')
            return redirect('maintenance_request_detail', request_id=maintenance_request.id)
    else:
        form = MaintenanceStatusUpdateForm(instance=maintenance_request)
    
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
                return redirect('maintenance_requests')
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
        'techs': ['Django', 'Python', 'Tailwind CSS', 'SQLite', 'ReportLab', 'Chart.js', 'Font Awesome', 'Google Translate'],
    }
    return render(request, 'dashboardd/about.html', context)


@login_required
def test_sms(request):
    """Dev-only endpoint to test Beem SMS. Remove or restrict before going live."""

    if not settings.DEBUG:
        return JsonResponse({'error': 'Only available in DEBUG mode'}, status=403)

    phone = request.GET.get('phone', '').strip()
    message = request.GET.get('message', 'Maghettoni SMS test - inafanya kazi!')

    if not phone:
        return JsonResponse({
            'usage': '/dashboard/test-sms/?phone=255712345678&message=Hello',
            'error': 'phone parameter required'
        }, status=400)

    import requests as req_lib
    from requests.auth import HTTPBasicAuth

    # Normalise phone
    phone_norm = phone.lstrip('+')
    if phone_norm.startswith('0'):
        phone_norm = '255' + phone_norm[1:]

    payload = {
        "source_addr": settings.BEEM_SENDER_ID,
        "encoding": 0,
        "message": message,
        "recipients": [{"recipient_id": 1, "dest_addr": phone_norm}],
    }

    try:
        resp = req_lib.post(
            "https://apisms.beem.africa/v1/send",
            json=payload,
            auth=HTTPBasicAuth(settings.BEEM_API_KEY, settings.BEEM_SECRET_KEY),
            timeout=10,
        )
        return JsonResponse({
            'success': resp.status_code == 200,
            'beem_status': resp.status_code,
            'beem_response': resp.text,
            'phone_sent_to': phone_norm,
            'sender_id': settings.BEEM_SENDER_ID,
            'api_key_set': bool(settings.BEEM_API_KEY),
            'secret_key_set': bool(settings.BEEM_SECRET_KEY),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
