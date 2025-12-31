from django.contrib import admin
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'property_type', 'units', 'owner', 'created_at']
    list_filter = ['property_type', 'created_at']
    search_fields = ['name', 'address']
    raw_id_fields = ['owner']

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'property', 'bedrooms', 'bathrooms', 'monthly_rent', 'is_occupied']
    list_filter = ['is_occupied', 'property']
    search_fields = ['unit_number', 'property__name']
    raw_id_fields = ['property']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'property', 'unit', 'email', 'phone', 'move_in_date']
    list_filter = ['property', 'move_in_date']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    raw_id_fields = ['property', 'unit', 'user']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'property', 'amount', 'payment_date', 'status', 'payment_method']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['tenant__first_name', 'tenant__last_name', 'reference_number']
    raw_id_fields = ['tenant', 'property']

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'property', 'unit', 'tenant', 'priority', 'status', 'reported_date']
    list_filter = ['priority', 'status', 'reported_date']
    search_fields = ['title', 'description', 'property__name']
    raw_id_fields = ['property', 'unit', 'tenant']