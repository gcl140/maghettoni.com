from .models import *
from datetime import datetime

def context(request):
    return {
        'year': datetime.now().year,
        'due_payments_count': Payment.objects.filter(tenant__property__owner=request.user, due_date__lt=datetime.now().date(), status__in=['failed', 'pending']).count(),
        'pending_maintenance_count': MaintenanceRequest.objects.filter(property__owner=request.user,status='pending').count(),
        }
