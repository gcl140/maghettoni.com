from django.urls import path
from . import views, api

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    
    # Properties
    path('properties/', views.property_list, name='property_list'),
    path('properties/add/', views.property_edit, name='add_property'),
    path('properties/edit/<int:property_id>/', views.property_edit, name='property_edit'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/<int:property_id>/documents/<int:document_id>/delete/', views.property_document_delete, name='property_document_delete'),
    path('properties/delete/<int:property_id>/', views.property_delete, name='property_delete'),
    path('properties/units/<int:property_id>/', views.property_units, name='property_units'),

    path('properties/<int:property_id>/units/', views.property_units, name='property_units'),
    path('properties/<int:property_id>/units/add/', views.unit_edit, name='unit_add'),
    path('properties/<int:property_id>/units/<int:unit_id>/edit/', views.unit_edit, name='unit_edit'),
    path('properties/<int:property_id>/units/<int:unit_id>/delete/', views.unit_delete, name='unit_delete'),
    
    path('api/location/', views.location_api, name='location_api'),
    
    # Tenants
    path('tenants/export/csv/', views.tenants_export_csv, name='tenants_export_csv'),
    path('tenants/export/pdf/', views.tenants_export_pdf, name='tenants_export_pdf'),
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/add/', views.tenant_edit, name='add_tenant'),
    path('tenants/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('tenants/edit/<int:tenant_id>/', views.tenant_edit, name='tenant_edit'),
    path('api/properties/<int:property_id>/units/available/', views.get_available_units, name='available_units'),
    path('tenants/<int:tenant_id>/activate/', views.tenant_activate, name='tenant_activate'),
    path('tenants/<int:tenant_id>/deactivate/', views.tenant_deactivate, name='tenant_deactivate'),
    path('tenants/<int:tenant_id>/delete/', views.tenant_delete, name='tenant_delete'),
    
    # Payments URLs
    path('payments/export/csv/', views.payments_export_csv, name='payments_export_csv'),
    path('payments/export/pdf/', views.payments_export_pdf, name='payments_export_pdf'),
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/create/', views.payment_edit, name='payment_create'),
    path('payments/<int:payment_id>/receipt/', views.payment_receipt_pdf, name='payment_receipt'),
    path('payments/<int:payment_id>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('api/tenants/<int:tenant_id>/details/', views.get_tenant_details, name='tenant_details'),
    
    # Maintenance URLs
    path('maintenance/export/csv/', views.maintenance_export_csv, name='maintenance_export_csv'),
    path('maintenance/export/pdf/', views.maintenance_export_pdf, name='maintenance_export_pdf'),
    path('maintenance/', views.maintenance_requests_list, name='maintenance_requests'),
    path('maintenance/create/', views.maintenance_request_edit, name='maintenance_request_create'),
    path('maintenance/<int:request_id>/edit/', views.maintenance_request_edit, name='maintenance_request_edit'),
    path('maintenance/<int:request_id>/', views.maintenance_request_detail, name='maintenance_request_detail'),
    path('api/properties/<int:property_id>/units-tenants/', views.get_property_units_tenants, name='property_units_tenants'),

    
    path('search/', views.search_results, name='search_results'),
    path('search/quick/', views.quick_search, name='quick_search'),

    # Dev only — remove before going live
    path('test-sms/', views.test_sms, name='test_sms'),

    # JSON API
    path('api/v1/properties/', api.api_properties, name='api_properties'),
    path('api/v1/properties/<int:property_id>/', api.api_property_detail, name='api_property_detail'),
    path('api/v1/tenants/', api.api_tenants, name='api_tenants'),
    path('api/v1/tenants/<int:tenant_id>/', api.api_tenant_detail, name='api_tenant_detail'),
    path('api/v1/payments/', api.api_payments, name='api_payments'),
    path('api/v1/payments/<int:payment_id>/', api.api_payment_detail, name='api_payment_detail'),
    path('api/v1/maintenance/', api.api_maintenance, name='api_maintenance'),
    path('api/v1/maintenance/<int:request_id>/', api.api_maintenance_detail, name='api_maintenance_detail'),

    # Notifications
    path('api/v1/notifications/', api.api_notifications, name='api_notifications'),

    # SMS reminders
    path('api/v1/payments/<int:payment_id>/remind/', api.api_payment_remind, name='api_payment_remind'),
    path('api/v1/maintenance/<int:request_id>/notify/', api.api_maintenance_notify, name='api_maintenance_notify'),
]