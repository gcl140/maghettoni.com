from django.urls import path
from . import views, api

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

    # Notifications
    path('notifications/', views.tenant_notifications, name='tenant_notifications'),

    # Invite accept (public — no login required)
    path('invite/<uuid:token>/', views.invite_accept, name='tenant_invite_accept'),

    # API
    path('api/dashboard/', api.api_tenant_dashboard, name='api_tenant_dashboard'),
    path('api/calendar/', api.api_tenant_calendar, name='api_tenant_calendar'),
    path('api/notifications/', api.api_tenant_notifications, name='api_tenant_notifications'),
]
