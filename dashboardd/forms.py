from django import forms
from django.utils import timezone
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'property_type', 'units']

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['property', 'unit_number', 'bedrooms', 'bathrooms', 'square_feet', 'monthly_rent', 'description']

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['property', 'unit', 'first_name', 'last_name', 'email', 'phone', 
                  'emergency_contact', 'emergency_phone', 'lease_start_date', 'lease_end_date']
        widgets = {
            'lease_start_date': forms.DateInput(attrs={'type': 'date'}),
            'lease_end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter properties to only those owned by the user
            self.fields['property'].queryset = Property.objects.filter(owner=user)
            
            # Filter units to only those from user's properties
            self.fields['unit'].queryset = Unit.objects.filter(property__owner=user, is_occupied=False)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'property', 'amount', 'payment_date', 'due_date', 
                  'payment_method', 'status', 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter to only user's properties and tenants
            self.fields['property'].queryset = Property.objects.filter(owner=user)
            self.fields['tenant'].queryset = Tenant.objects.filter(property__owner=user)

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['property', 'unit', 'tenant', 'title', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter to only user's properties, units, and tenants
            self.fields['property'].queryset = Property.objects.filter(owner=user)
            self.fields['unit'].queryset = Unit.objects.filter(property__owner=user)
            self.fields['tenant'].queryset = Tenant.objects.filter(property__owner=user)