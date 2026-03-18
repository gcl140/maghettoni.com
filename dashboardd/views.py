import json
import csv
import io
import urllib.request
import urllib.parse
from datetime import timedelta
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Sum, Count, Q, Min, Max, Avg
from django.db.models.functions import TruncMonth
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from .models import Property, PropertyImage, Unit, Tenant, Payment, MaintenanceRequest, Notification, TenantInvite
from .forms import (
    PropertyForm,
    PropertyDocumentForm,
    UnitForm,
    TenantForm,
    PaymentForm,
    MaintenanceRequestForm,
    MaintenanceStatusUpdateForm,
)
from django.contrib.auth.decorators import login_required
from functools import wraps

def landlord_required(view_func):
    """Allow only authenticated users with is_landlord=True."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not getattr(request.user, 'is_landlord', False):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped

def _send_tenant_invite(request, tenant):
    """
    Create a TenantInvite, then deliver the invite link + temp credentials
    via BOTH email and SMS.  The landlord never sees the token or password.
    """
    from django.core.mail import EmailMessage as _Email
    from .services import send_sms

    invite = TenantInvite.create_for_tenant(tenant, hours=72)

    scheme = 'https' if request.is_secure() else 'http'
    host   = request.get_host()
    link   = f"{scheme}://{host}/tenant/invite/{invite.token}/"

    # ── Email (full details) ─────────────────────────────────────────────
    email_body = (
        f"Hello {tenant.first_name},\n\n"
        f"You have been invited to the Maghettoni Tenant Portal by your landlord.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Username : {tenant.phone}\n"
        f"  Temporary Password : {invite.temp_password}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Click the link below to accept your invitation and set a new password:\n"
        f"{link}\n\n"
        f"This link will expire in 72 hours.\n\n"
        f"NOTE: Do not share this password with anyone.\n"
        f"Once you accept the invite you can change your password at any time.\n\n"
        f"— The Maghettoni Team"
    )
    try:
        _Email(
            subject="Your Maghettoni Tenant Portal Invitation",
            body=email_body,
            to=[tenant.email],
        ).send(fail_silently=False)
    except Exception:
        pass

    # ── SMS (concise — credentials + link) ──────────────────────────────
    if tenant.phone:
        sms_body = (
            f"Hello {tenant.first_name}! You have been invited to Maghettoni Tenant Portal.\n"
            f"Username: {tenant.phone}\n"
            f"Password: {invite.temp_password}\n"
            f"Accept here: {link}\n"
            f"(Expires in 72 hours. Do not share your password.)"
        )
        try:
            send_sms(tenant.phone, sms_body)
        except Exception:
            pass


def _notify(user, title, message):
    """Create an in-app notification, skipping duplicates within 60 seconds."""
    cutoff = timezone.now() - timedelta(seconds=60)
    if Notification.objects.filter(
        recipient=user, title=title, message=message, created_at__gte=cutoff
    ).exists():
        return
    Notification.objects.create(recipient=user, title=title, message=message)


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


@landlord_required
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


@landlord_required
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


@landlord_required
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
            'type': 'Property',
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
            'type': 'Tenant',
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
            'type': 'Payment',
            'name': f"TZS {payment.amount}",
            'detail': payment.tenant.full_name(),
            # 'url': '#',
            'url': reverse('payment_detail', args=[payment.id]),
            'icon': 'money-bill'
        })

    return JsonResponse({'results': results})


@landlord_required
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


@landlord_required
def property_delete(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        if property_obj.units_list.filter(is_occupied=True).exists():
            messages.error(request, 'Cannot delete a property with occupied units. Move out all tenants first.')
            return redirect('property_detail', property_id=property_id)
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
@landlord_required
@csrf_exempt
def location_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        lat = data.get("lat")
        lng = data.get("lng")

        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        address = None

        if api_key:
            params = urllib.parse.urlencode({'latlng': f"{lat},{lng}", 'key': api_key})
            url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
            with urllib.request.urlopen(url, timeout=5) as resp:
                geo = json.loads(resp.read().decode())
            if geo.get('status') == 'OK' and geo.get('results'):
                address = geo['results'][0]['formatted_address']

        if not address:
            address = f"{float(lat):.6f}, {float(lng):.6f}"

        return JsonResponse({"address": address, "lat": lat, "lng": lng})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@landlord_required
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

            # Handle address from JS-populated hidden inputs
            addr_name = request.POST.get('address_name', '').strip()
            addr_lat = request.POST.get('address_lat', '').strip()
            addr_lng = request.POST.get('address_lng', '').strip()
            addr_source = request.POST.get('address_source', '').strip()
            if addr_name:
                property_obj.address = addr_name
                try:
                    property_obj.address_data = {
                        'name': addr_name,
                        'lat': float(addr_lat) if addr_lat else None,
                        'lng': float(addr_lng) if addr_lng else None,
                        'source': addr_source or None,
                    }
                except (ValueError, TypeError):
                    property_obj.address_data = {'name': addr_name}
            elif not property_obj.address:
                # New property submitted without address — require it
                form.add_error(None, 'Please set the property location before saving.')
                form = form  # fall through to re-render

            if form.is_valid():
                property_obj.save()
                # Handle multiple image uploads
                new_images = request.FILES.getlist('new_images')
                existing_count = property_obj.images.count()
                slots = max(0, 5 - existing_count)
                if new_images:
                    if len(new_images) > slots:
                        messages.warning(request, f'Only {slots} more image(s) allowed (max 5). First {slots} uploaded.')
                    for i, img in enumerate(new_images[:slots]):
                        PropertyImage.objects.create(property=property_obj, image=img, order=existing_count + i)
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
        'existing_images': property_obj.images.all() if property_obj else [],
        'slots_remaining': max(0, 5 - property_obj.images.count()) if property_obj else 5,
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'has_occupied_units': property_obj.units_list.filter(is_occupied=True).exists() if property_obj else False,
    }
    return render(request, 'properties/edit.html', context)


@landlord_required
def delete_property_image(request, image_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    img = get_object_or_404(PropertyImage, pk=image_id, property__owner=request.user)
    img.image.delete(save=False)
    img.delete()
    return JsonResponse({'ok': True})


@landlord_required
def property_units(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all()
    
    context = {
        'property': property_obj,
        'units': units,
    }
    
    return render(request, 'properties/units.html', context)


@landlord_required
def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    doc_search = request.GET.get('doc_q', '').strip()
    doc_type = request.GET.get('doc_type', 'all').strip().lower()

    if request.method == 'POST':
        upload_form = PropertyDocumentForm(request.POST, request.FILES)
        if upload_form.is_valid():
            document = upload_form.save(commit=False)
            document.property = property_obj
            document.uploaded_by = request.user
            previous = property_obj.documents.filter(title=document.title).order_by('-version', '-uploaded_at').first()
            if previous:
                document.version = previous.version + 1
                document.previous_version = previous
            document.save()
            if document.version > 1:
                messages.success(request, f'Document uploaded as version v{document.version}.')
            else:
                messages.success(request, 'Document uploaded successfully.')
            return redirect('property_detail', property_id=property_obj.id)
        messages.error(request, 'Please fix the document upload errors below.')
    else:
        upload_form = PropertyDocumentForm()

    units = property_obj.units_list.all()
    tenants = property_obj.tenants.all()
    documents_qs = property_obj.documents.select_related('uploaded_by').all()

    if doc_search:
        documents_qs = documents_qs.filter(
            Q(title__icontains=doc_search) |
            Q(notes__icontains=doc_search) |
            Q(file__icontains=doc_search)
        )

    if doc_type == 'image':
        documents_qs = documents_qs.filter(
            Q(file__iendswith='.jpg') |
            Q(file__iendswith='.jpeg') |
            Q(file__iendswith='.png') |
            Q(file__iendswith='.gif') |
            Q(file__iendswith='.webp')
        )
    elif doc_type == 'pdf':
        documents_qs = documents_qs.filter(file__iendswith='.pdf')
    elif doc_type == 'doc':
        documents_qs = documents_qs.filter(
            Q(file__iendswith='.doc') |
            Q(file__iendswith='.docx') |
            Q(file__iendswith='.txt')
        )
    elif doc_type == 'other':
        documents_qs = documents_qs.exclude(
            Q(file__iendswith='.jpg') |
            Q(file__iendswith='.jpeg') |
            Q(file__iendswith='.png') |
            Q(file__iendswith='.gif') |
            Q(file__iendswith='.webp') |
            Q(file__iendswith='.pdf') |
            Q(file__iendswith='.doc') |
            Q(file__iendswith='.docx') |
            Q(file__iendswith='.txt')
        )

    documents = []
    seen_titles = set()
    for doc in documents_qs.order_by('-version', '-uploaded_at'):
        title_key = doc.title.strip().lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        doc.history_versions = list(
            property_obj.documents
            .select_related('uploaded_by')
            .filter(title=doc.title, version__lt=doc.version)
            .order_by('-version', '-uploaded_at')
        )
        documents.append(doc)
    
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
    
    property_images = list(property_obj.images.all())

    context = {
        'property': property_obj,
        'property_images': property_images,
        'units': units,
        'tenants': tenants,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacancy_rate': round(vacancy_rate, 2),
        'recent_payments': recent_payments,
        'maintenance_requests': maintenance_requests,
        'documents': documents,
        'upload_form': upload_form,
        'doc_search': doc_search,
        'doc_type': doc_type,
    }

    return render(request, 'properties/detail.html', context)


@landlord_required
def property_document_delete(request, property_id, document_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    document = get_object_or_404(property_obj.documents, id=document_id)

    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully.')

    return redirect('property_detail', property_id=property_obj.id)



# @login_required
# def tenant_list(request):
#     tenants = Tenant.objects.filter(property__owner=request.user)
#     return render(request, 'tenants/list.html', {'tenants': tenants})


@landlord_required
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

@landlord_required
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
    response['Content-Disposition'] = 'attachment; filename="tenants.csv"'
    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Email', 'Phone', 'Property', 'Unit', 'Status', 'Move-in Date'])
    for t in qs:
        writer.writerow([
            t.full_name() if hasattr(t, 'full_name') else f'{t.first_name} {t.last_name}',
            t.email or '',
            t.phone or '',
            t.property.name if t.property else '',
            t.unit.unit_number if t.unit else '',
            t.get_status_display(),
            t.move_in_date or '',
        ])
    return response

@landlord_required
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

    headers = ['Full Name', 'Email', 'Phone', 'Property', 'Unit', 'Status', 'Move-in Date']
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

    buf = _build_pdf('Tenants', headers, rows)
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


@landlord_required
def tenant_activate(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    tenant.status = 'active'
    tenant.save()
    name = tenant.full_name()
    _notify(request.user, f'Mkazi Amewashwa: {name}',
            f'{name} amewashwa rasmi katika {tenant.property.name}.')
    messages.success(request, f'{name} has been activated!')
    return redirect('tenant_detail', tenant_id=tenant.id)

@landlord_required
def tenant_deactivate(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    tenant.status = 'inactive'
    tenant.save()
    name = tenant.full_name()
    _notify(request.user, f'Mkazi Amezimwa: {name}',
            f'{name} amezimwa katika {tenant.property.name}.')
    messages.success(request, f'{name} has been deactivated!')
    return redirect('tenant_detail', tenant_id=tenant.id)

@landlord_required
def tenant_delete(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    tenant_name = tenant.full_name()
    tenant.delete()
    messages.success(request, f'Tenant {tenant_name} has been removed!')
    return redirect('tenant_list')

@landlord_required
def tenant_detail(request, tenant_id):
    import calendar as _cal
    from datetime import date as _date
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

    # Eligibility calculation
    eligibility = None
    if tenant.unit and tenant.unit.monthly_rent:
        monthly_rent = tenant.unit.monthly_rent
        months_paid = int(total_payments / monthly_rent) if monthly_rent else 0
        eligible_until = None
        if months_paid > 0 and tenant.move_in_date:
            start = tenant.move_in_date
            m = start.month + months_paid - 1
            year = start.year + m // 12
            month = m % 12 + 1
            last_day = _cal.monthrange(year, month)[1]
            eligible_until = _date(year, month, min(start.day, last_day))
        days_left = (eligible_until - today).days if (eligible_until and eligible_until >= today) else 0
        eligibility = {
            'months_paid': months_paid,
            'eligible_until': eligible_until,
            'days_left': days_left,
            'monthly_rent': monthly_rent,
            'min_rental_months': tenant.unit.min_rental_months,
            'min_amount': monthly_rent * tenant.unit.min_rental_months,
        }

    context = {
        'tenant': tenant,
        'payments': payments,
        'maintenance_requests': maintenance_requests,
        'total_payments': total_payments,
        'pending_payments': pending_payments,
        'active_maintenance': active_maintenance,
        'days_in_tenancy': days_in_tenancy,
        'today': today,
        'eligibility': eligibility,
    }
    return render(request, 'tenants/detail.html', context)


@landlord_required
def tenant_edit(request, tenant_id=None):
    """
    Combined view for adding and editing tenants
    """
    # If tenant_id is provided, we're editing; otherwise, we're adding
    if tenant_id:
        tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
        is_edit = True
        title = "Edit Tenant"
        success_message = "Tenant updated successfully!"
    else:
        tenant = None
        is_edit = False
        title = "Add New Tenant"
        success_message = "Tenant added successfully!"

    # Verified tenants (with an active portal account) are locked — only status changes allowed
    is_locked = bool(is_edit and tenant.user_id and tenant.user.is_verified)

    if request.method == 'POST':
        if is_locked:
            # Only allow status update for verified tenants
            new_status = request.POST.get('status', tenant.status)
            if new_status != tenant.status:
                tenant.status = new_status
                tenant.save(update_fields=['status'])
                _notify(request.user, f'Hali ya Mkazi Imebadilishwa: {tenant.full_name()}',
                        f'Hali ya {tenant.full_name()} imebadilishwa hadi {new_status}.')
                messages.success(request, "Tenant status updated.")
            else:
                messages.info(request, "No changes made.")
            return redirect('tenant_detail', tenant_id=tenant.id)

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

            if is_edit:
                _notify(request.user, f'Tenant Updated: {tenant.full_name()}',
                        f'{tenant.full_name()}\'s details have been updated.')
            else:
                unit_label = f', unit {tenant.unit.unit_number}' if tenant.unit else ''
                _notify(request.user, f'New Tenant: {tenant.full_name()}',
                        f'{tenant.full_name()} has been added to {tenant.property.name}{unit_label}.')
                # Send invite email to the new tenant
                _send_tenant_invite(request, tenant)
                messages.info(
                    request,
                    f'Invite sent to {tenant.email}. '
                    'The tenant must accept within 72 hours.'
                )

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
        'is_locked': is_locked,
        'title': title,
        'tenant': tenant,
    }
    return render(request, 'tenants/edit.html', context)

@landlord_required
def tenant_resend_invite(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    if tenant.user and tenant.user.is_verified:
        messages.warning(request, f"{tenant.full_name()} has already verified their account — no invite needed.")
    else:
        _send_tenant_invite(request, tenant)
        messages.success(request, f"Invite re-sent to {tenant.email}.")
    return redirect('tenant_detail', tenant_id=tenant.id)


@landlord_required
def tenant_lease_print(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    lang = request.GET.get('lang', 'en')
    if lang not in ('en', 'sw'):
        lang = 'en'
    # Calculate eligibility from payments (same logic as tenant_detail)
    eligibility = None
    if tenant.unit and tenant.unit.monthly_rent:
        from django.db.models import Sum as _Sum
        import calendar as _lcal
        from datetime import date as _date
        monthly_rent = tenant.unit.monthly_rent
        total_paid = tenant.payments.filter(status='completed').aggregate(
            total=_Sum('amount')
        )['total'] or 0
        months_paid = int(total_paid / monthly_rent) if monthly_rent else 0
        eligible_until = None
        if months_paid > 0 and tenant.move_in_date:
            start = tenant.move_in_date
            m = start.month + months_paid - 1
            yr = start.year + m // 12
            mo = m % 12 + 1
            last_day = _lcal.monthrange(yr, mo)[1]
            eligible_until = _date(yr, mo, min(start.day, last_day))
        eligibility = {'months_paid': months_paid, 'eligible_until': eligible_until}
    return render(request, 'tenants/lease_print.html', {
        'tenant': tenant,
        'lang': lang,
        'eligibility': eligibility,
    })


# Add this to views.py if you want dynamic unit filtering
@landlord_required
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

@landlord_required
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

@landlord_required
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
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tenant', 'Property', 'Amount (TZS)', 'Payment Date', 'Due Date', 'Status', 'Reference Number'])
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

@landlord_required
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

    headers = ['Tenant', 'Property', 'Amount (TZS)', 'Payment Date', 'Due Date', 'Status', 'Reference']
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

    buf = _build_pdf('Payments', headers, rows)
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="payments.pdf"'})

@landlord_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, property__owner=request.user)

    if request.method == 'POST':
        if 'mark_paid' in request.POST:
            payment.status = 'completed'
            payment.landlord_confirmed = True
            payment.payment_date = timezone.now().date()
            payment.save()
            _notify(request.user, f'Payment Completed: {payment.tenant.full_name()}',
                    f'{payment.tenant.full_name()} paid TZS. {payment.amount:,.0f} '
                    f'({payment.property.name}).')
            messages.success(request, 'Payment marked as completed!')
            return redirect('payment_detail', payment_id=payment.id)
        elif 'status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in ['pending', 'completed', 'failed', 'refunded']:
                payment.status = new_status
                payment.save()
                status_msgs = {
                    'completed': f'Payment Completed: {payment.tenant.full_name()}',
                    'failed':    f'Payment Failed: {payment.tenant.full_name()}',
                    'refunded':  f'Payment Refunded: {payment.tenant.full_name()}',
                    'pending':   f'Payment Reverted to Pending: {payment.tenant.full_name()}',
                }
                _notify(request.user, status_msgs.get(new_status, 'Payment Status Changed'),
                        f'TZS. {payment.amount:,.0f} — new status: {payment.get_status_display()} '
                        f'({payment.property.name}).')
                messages.success(request, f'Status updated to {payment.get_status_display()}.')
            return redirect('payment_detail', payment_id=payment.id)

    context = {
        'payment': payment,
        'is_overdue': payment.due_date and payment.due_date < timezone.now().date() and payment.status == 'pending',
    }
    return render(request, 'payments/detail.html', context)

@landlord_required
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

@landlord_required
def payment_edit(request, payment_id=None):
    """
    Combined view for adding and editing payments
    """
    # If payment_id is provided, we're editing; otherwise, we're adding
    if payment_id:
        payment = get_object_or_404(Payment, id=payment_id, property__owner=request.user)
        is_edit = True
        title = "Edit Payment Record"
        success_message = "Payment updated successfully!"
    else:
        payment = None
        is_edit = False
        title = "Record New Payment"
        success_message = "Payment recorded successfully!"
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            
            # If marking as completed and payment_date is today's default, update to actual date
            if payment.status == 'completed' and payment.payment_date == timezone.now().date():
                payment.payment_date = timezone.now().date()
            
            payment.save()

            if is_edit:
                _notify(request.user, f'Payment Updated: {payment.tenant.full_name()}',
                        f'Payment record of TZS. {payment.amount:,.0f} has been updated '
                        f'({payment.property.name}).')
            else:
                _notify(request.user, f'New Payment: {payment.tenant.full_name()}',
                        f'Payment of TZS. {payment.amount:,.0f} recorded for '
                        f'{payment.tenant.full_name()} — {payment.property.name}.')

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

@landlord_required
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

@landlord_required
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
    response['Content-Disposition'] = 'attachment; filename="maintenance.csv"'
    writer = csv.writer(response)
    writer.writerow(['Title', 'Property', 'Unit', 'Tenant', 'Priority', 'Status', 'Date', 'Cost (TZS)'])
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

@landlord_required
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

    headers = ['Title', 'Property', 'Unit', 'Tenant', 'Priority', 'Status', 'Date', 'Cost (TZS)']
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

    buf = _build_pdf('Maintenance', headers, rows)
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="maintenance.pdf"'})

@never_cache
@landlord_required
def maintenance_request_detail(request, request_id):
    maintenance_request = get_object_or_404(
        MaintenanceRequest, id=request_id, property__owner=request.user
    )
    
    if request.method == 'POST':
        form = MaintenanceStatusUpdateForm(request.POST, instance=maintenance_request)
        if form.is_valid():
            old_status = maintenance_request.status
            maintenance_request = form.save(commit=False)
            if maintenance_request.status == 'completed' and not maintenance_request.completed_date:
                maintenance_request.completed_date = timezone.now()
            maintenance_request.save()
            if maintenance_request.status != old_status:
                if maintenance_request.status == 'completed':
                    _notify(request.user, f'Maintenance Completed: {maintenance_request.title}',
                            f'Request "{maintenance_request.title}" at '
                            f'{maintenance_request.property.name} is now complete.')
                else:
                    _notify(request.user, f'Maintenance Status Changed: {maintenance_request.title}',
                            f'"{maintenance_request.title}" — new status: '
                            f'{maintenance_request.get_status_display()} '
                            f'({maintenance_request.property.name}).')
            messages.success(request, 'Maintenance request updated!')
            return redirect('maintenance_request_detail', request_id=maintenance_request.id)
    else:
        form = MaintenanceStatusUpdateForm(instance=maintenance_request)
    
    context = {
        'request': maintenance_request,
        'form': form,
    }
    return render(request, 'maintenance/detail.html', context)


@landlord_required
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

            if is_edit:
                _notify(request.user, f'Maintenance Updated: {maintenance_request.title}',
                        f'Request "{maintenance_request.title}" has been updated '
                        f'({maintenance_request.property.name}).')
            else:
                priority_label = maintenance_request.get_priority_display()
                _notify(request.user, f'New Maintenance Request: {maintenance_request.title}',
                        f'"{maintenance_request.title}" submitted by '
                        f'{maintenance_request.tenant.full_name()} — {maintenance_request.property.name} '
                        f'[{priority_label}].')

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


@landlord_required
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


@landlord_required
def property_units(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all()

    # Calculate statistics
    total_units = units.count()
    occupied_units = units.filter(is_occupied=True).count()
    vacant_units = total_units - occupied_units
    agg = units.aggregate(
        total=Sum('monthly_rent'),
        min_rent=Min('monthly_rent'),
        max_rent=Max('monthly_rent'),
        avg_rent=Avg('monthly_rent'),
    )
    total_monthly_rent = agg['total'] or 0

    context = {
        'property': property_obj,
        'units': units,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'total_monthly_rent': total_monthly_rent,
        'min_rent': agg['min_rent'] or 0,
        'max_rent': agg['max_rent'] or 0,
        'avg_rent': round(agg['avg_rent'] or 0, 2),
        'occupancy_rate': round((occupied_units / total_units * 100), 1) if total_units else 0,
    }

    return render(request, 'properties/units.html', context)


@landlord_required
def units_export_csv(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all().order_by('unit_number')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{property_obj.name}-units.csv"'
    writer = csv.writer(response)
    writer.writerow(['Unit', 'Bedrooms', 'Bathrooms', 'Sq Ft', 'Monthly Rent', 'Status', 'Description'])
    for u in units:
        writer.writerow([
            u.unit_number,
            u.bedrooms,
            u.bathrooms,
            u.square_feet or '',
            u.monthly_rent,
            'Occupied' if u.is_occupied else 'Vacant',
            u.description or '',
        ])
    return response


@landlord_required
def units_export_pdf(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    units = property_obj.units_list.all().order_by('unit_number')

    headers = ['Unit', 'Bedrooms', 'Bathrooms', 'Sq Ft', 'Monthly Rent (TZS. )', 'Status']
    rows = [[
        u.unit_number,
        u.bedrooms,
        u.bathrooms,
        u.square_feet or '-',
        u.monthly_rent,
        'Occupied' if u.is_occupied else 'Vacant',
    ] for u in units]

    buf = _build_pdf(f'{property_obj.name} — Units', headers, rows)
    filename = f"{property_obj.name}-units.pdf"
    return HttpResponse(buf, content_type='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@landlord_required
@require_GET
def units_vacancy_alert(request, property_id):
    """Create a notification listing the current vacant units for this property."""
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    vacant = property_obj.units_list.filter(is_occupied=False).order_by('unit_number')

    if not vacant.exists():
        return JsonResponse({'status': 'ok', 'message': 'No vacant units right now — all units are occupied!'})

    unit_list = ', '.join(f'Unit {u.unit_number}' for u in vacant)
    Notification.objects.create(
        recipient=request.user,
        title=f'Vacancy Alert — {property_obj.name}',
        message=f'{vacant.count()} vacant unit(s): {unit_list}',
    )
    return JsonResponse({
        'status': 'ok',
        'count': vacant.count(),
        'message': f'Alert created — {vacant.count()} vacant unit(s): {unit_list}',
    })

@landlord_required
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
        success_message = f"Unit {unit.unit_number} updated successfully!"
    else:
        unit = None
        is_edit = False
        title = "Add New Unit"
        success_message = "New unit added successfully!"
    
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.property = property_obj

            try:
                amenities = json.loads(request.POST.get('amenities', '{}'))
            except (json.JSONDecodeError, ValueError):
                amenities = {}
            unit.amenities = amenities
            # Keep dedicated model fields in sync with amenities JSON
            if 'bedrooms'    in amenities: unit.bedrooms    = amenities['bedrooms']    or None
            if 'bathrooms'   in amenities: unit.bathrooms   = amenities['bathrooms']   or None
            if 'square_feet' in amenities: unit.square_feet = amenities['square_feet'] or None

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

    active_tenant = None
    if unit:
        active_tenant = unit.current_tenant.filter(status='active').first()

    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
        'property': property_obj,
        'unit': unit,
        'existing_amenities': json.dumps(unit.amenities if unit and unit.amenities else {}),
        'active_tenant': active_tenant,
    }
    return render(request, 'properties/unit_edit.html', context)

@landlord_required
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
@landlord_required
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
@landlord_required
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
