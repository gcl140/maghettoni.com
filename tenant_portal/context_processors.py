from .models import TenantNotification


def tenant_context(request):
    """Inject tenant portal context into all tenant_portal templates."""
    if not request.user.is_authenticated:
        return {}
    if not hasattr(request.user, 'tenant_profile') or request.user.tenant_profile is None:
        return {}
    tenant = request.user.tenant_profile
    unread = TenantNotification.objects.filter(tenant=tenant, is_read=False).count()
    return {
        'tenant': tenant,
        'tenant_unread_count': unread,
    }
