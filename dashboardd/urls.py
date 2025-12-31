from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    
    # Properties
    path('properties/', views.property_list, name='property_list'),
    path('properties/add/', views.property_edit, name='add_property'),
    path('properties/edit/<int:property_id>/', views.property_edit, name='property_edit'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/delete/<int:property_id>/', views.property_delete, name='property_delete'),
    path('properties/units/<int:property_id>/', views.property_units, name='property_units'),

    path('properties/<int:property_id>/units/', views.property_units, name='property_units'),
    path('properties/<int:property_id>/units/add/', views.unit_edit, name='unit_add'),
    path('properties/<int:property_id>/units/<int:unit_id>/edit/', views.unit_edit, name='unit_edit'),
    path('properties/<int:property_id>/units/<int:unit_id>/delete/', views.unit_delete, name='unit_delete'),
    
    path('api/location/', views.location_api, name='location_api'),
    
    # Tenants
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/add/', views.tenant_edit, name='add_tenant'),
    path('tenants/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('tenants/edit/<int:tenant_id>/', views.tenant_edit, name='tenant_edit'),
    path('api/properties/<int:property_id>/units/available/', views.get_available_units, name='available_units'),


    # path('tenants/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('tenants/<int:tenant_id>/activate/', views.tenant_activate, name='tenant_activate'),
    path('tenants/<int:tenant_id>/deactivate/', views.tenant_deactivate, name='tenant_deactivate'),
    path('tenants/<int:tenant_id>/delete/', views.tenant_delete, name='tenant_delete'),
    
    # Payments URLs
    path('payments/', views.payments_list, name='payments_list'),
    # path('payments/create/', views.payment_create, name='payment_create'),

    path('payments/create/', views.payment_edit, name='payment_create'),
    path('payments/<int:payment_id>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('api/tenants/<int:tenant_id>/details/', views.get_tenant_details, name='tenant_details'),

    
    # Maintenance URLs
    path('maintenance/', views.maintenance_requests_list, name='maintenance_requests'),
    path('maintenance/create/', views.maintenance_request_edit, name='maintenance_request_create'),
    path('maintenance/<int:request_id>/edit/', views.maintenance_request_edit, name='maintenance_request_edit'),
    path('maintenance/<int:request_id>/', views.maintenance_request_detail, name='maintenance_request_detail'),
    path('api/properties/<int:property_id>/units-tenants/', views.get_property_units_tenants, name='property_units_tenants'),

    
]