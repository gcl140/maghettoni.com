from django.urls import path
from . import views, flutter_views

urlpatterns = [
    # Dashboard
    path('', views.tenant_dashboard, name='tenant_dashboard'),

    # Payments
    path('payments/', views.tenant_payments, name='tenant_payments'),
    path('payments/pay/', views.tenant_payment_initiate, name='tenant_payment_initiate'),
    path('payments/process/<uuid:token>/', views.tenant_payment_process, name='tenant_payment_process'),
    path('payments/status/<uuid:token>/', views.tenant_payment_status, name='tenant_payment_status'),

    # Maintenance
    path('maintenance/', views.tenant_maintenance, name='tenant_maintenance'),
    path('maintenance/report/', views.tenant_maintenance_create, name='tenant_maintenance_create'),
    path('maintenance/<int:request_id>/', views.tenant_maintenance_detail, name='tenant_maintenance_detail'),

    # Profile
    path('profile/', views.tenant_profile, name='tenant_profile'),
    path('profile/edit/', views.tenant_edit_profile, name='tenant_edit_profile'),
    path('tenancy/<int:tenancy_id>/notifications/toggle/', views.toggle_tenancy_notifications, name='toggle_tenancy_notifications'),

    # Notifications
    path('notifications/', views.tenant_notifications, name='tenant_notifications'),

    # Invite accept (public — no login required)
    path('invite/<uuid:token>/', views.invite_accept, name='tenant_invite_accept'),

    # API (Flutter + web JS)
    path('api/dashboard/', flutter_views.api_tenant_dashboard, name='api_tenant_dashboard'),
    path('api/calendar/', flutter_views.api_tenant_calendar, name='api_tenant_calendar'),
    path('api/notifications/', flutter_views.api_tenant_notifications, name='api_tenant_notifications'),
    path('api/maintenance/', flutter_views.api_tenant_maintenance, name='api_tenant_maintenance'),
    path('api/profile/', flutter_views.api_tenant_profile, name='api_tenant_profile'),
    path('api/profile/update/', flutter_views.api_tenant_update_profile, name='api_tenant_update_profile'),
    path('api/payments/', flutter_views.api_tenant_payments, name='api_tenant_payments'),
]
