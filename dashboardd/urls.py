from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Properties
    path('properties/', views.property_list, name='property_list'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    
    # Tenants
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/add/', views.add_tenant, name='add_tenant'),
    path('tenants/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    
    # Payments
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/record/', views.record_payment, name='record_payment'),
    
    # Maintenance
    path('maintenance/', views.maintenance_requests, name='maintenance_requests'),
    path('maintenance/create/', views.create_maintenance_request, name='create_maintenance_request'),
    path('dashboard/revenue-graph/', views.revenue_trend_graph, name='revenue_graph')

]