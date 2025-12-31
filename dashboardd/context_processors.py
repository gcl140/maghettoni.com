from .models import *
from datetime import datetime
from django.utils import timezone

def context(request):
    if not request.user.is_authenticated:
        return {
            'year': datetime.now().year,
            'due_payments_count': 0,
            'pending_maintenance_count': 0,
        }

    return {
        'year': datetime.now().year,
        'due_payments_count': Payment.objects.filter(tenant__property__owner=request.user,due_date__lt=timezone.now().date(),status__in=['failed', 'pending']).count(),
        'pending_maintenance_count': MaintenanceRequest.objects.filter(property__owner=request.user,status='pending').count(),
    }
