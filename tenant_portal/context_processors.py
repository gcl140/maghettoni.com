from .models import TenantNotification


def tenant_context(request):
    """Inject tenant portal context into all tenant_portal templates."""
    if not request.user.is_authenticated:
        return {}
    if not request.user.tenant_profiles.exists():
        return {}
    from .views import _get_tenant
    tenant = _get_tenant(request.user)
    if not tenant:
        return {}
    unread = TenantNotification.objects.filter(tenant=tenant, is_read=False).count()
    return {
        'tenant': tenant,
        'tenant_unread_count': unread,
    }
