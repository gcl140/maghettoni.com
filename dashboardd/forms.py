from django import forms
from django.utils import timezone
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'property_type', 'address', 'units', 'image']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

# class UnitForm(forms.ModelForm):
#     class Meta:
#         model = Unit
#         fields = ['property', 'unit_number', 'bedrooms', 'bathrooms', 'square_feet', 'monthly_rent', 'description']

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['unit_number', 'bedrooms', 'bathrooms', 'square_feet', 
                  'monthly_rent', 'is_occupied', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'monthly_rent': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes and placeholders
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-input'
            })
        
        # Specific field configurations
        self.fields['unit_number'].widget.attrs['placeholder'] = 'e.g., A101, Ground-1'
        self.fields['square_feet'].widget.attrs['placeholder'] = 'Square footage (optional)'
        self.fields['monthly_rent'].widget.attrs['placeholder'] = '0.00'
        self.fields['description'].widget.attrs['placeholder'] = 'Any special features or notes...'
        
        # Add help text
        self.fields['bedrooms'].help_text = 'Number of bedrooms'
        self.fields['bathrooms'].help_text = 'Number of bathrooms'
        self.fields['square_feet'].help_text = 'Optional - for record keeping'
        self.fields['monthly_rent'].help_text = 'Monthly rent amount in USD'
    
    def clean_unit_number(self):
        unit_number = self.cleaned_data['unit_number']
        # Ensure unit number is not empty
        if not unit_number.strip():
            raise forms.ValidationError("Unit number is required")
        return unit_number
    
    def clean_monthly_rent(self):
        monthly_rent = self.cleaned_data['monthly_rent']
        if monthly_rent < 0:
            raise forms.ValidationError("Rent cannot be negative")
        return monthly_rent
    
# from django import forms
# from django.utils import timezone
# from .models import Tenant

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['property', 'unit', 'first_name', 'last_name', 'email', 'phone', 
                  'emergency_contact', 'emergency_phone', 'move_in_date', 'move_out_date',
                  'status', 'profile_picture', 'notes']
        widgets = {
            'move_in_date': forms.DateInput(attrs={'type': 'date'}),
            'move_out_date': forms.DateInput(attrs={'type': 'date', 'class': 'optional-date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter properties to only those owned by the user
            self.fields['property'].queryset = Property.objects.filter(owner=self.user)
            
            # For new tenants, only show unoccupied units
            # For editing, show all units but filter differently
            if self.instance and self.instance.pk:
                # When editing, show all units from the property (including current one)
                if self.instance.property:
                    self.fields['unit'].queryset = Unit.objects.filter(
                        property=self.instance.property
                    ).order_by('unit_number')
            else:
                # When adding, only show unoccupied units
                self.fields['unit'].queryset = Unit.objects.filter(
                    property__owner=self.user, is_occupied=False
                ).order_by('unit_number')
        
        # Set today's date as default for move_in_date if creating new tenant
        if not self.instance.pk:
            self.fields['move_in_date'].initial = timezone.now().date()
        
        # Add placeholders and help text
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['email'].widget.attrs['placeholder'] = 'tenant@example.com'
        self.fields['phone'].widget.attrs['placeholder'] = '+255 xxx xxx xxx'
        self.fields['emergency_contact'].widget.attrs['placeholder'] = 'Emergency contact name'
        self.fields['emergency_phone'].widget.attrs['placeholder'] = '+255 xxx xxx xxx'
        
        # Add help text
        self.fields['phone'].help_text = 'Format: +255 xxx xxx xxx'
        self.fields['emergency_phone'].help_text = 'Optional - for emergencies only'
        self.fields['move_out_date'].help_text = 'Leave empty for current tenants'
    
    def clean(self):
        cleaned_data = super().clean()
        move_in_date = cleaned_data.get('move_in_date')
        move_out_date = cleaned_data.get('move_out_date')
        
        # Validate date logic
        if move_in_date and move_out_date:
            if move_out_date < move_in_date:
                raise forms.ValidationError({
                    'move_out_date': 'Move-out date cannot be before move-in date.'
                })
        
        # Validate email uniqueness (optional)
        email = cleaned_data.get('email')
        if email:
            existing = Tenant.objects.filter(email=email)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise forms.ValidationError({
                    'email': 'A tenant with this email already exists.'
                })
        
        return cleaned_data
    
# class TenantForm(forms.ModelForm):
#     class Meta:
#         model = Tenant
#         fields = ['property', 'unit', 'first_name', 'last_name', 'email', 'phone', 
#                   'emergency_contact', 'emergency_phone', 'move_in_date', 'move_out_date']
#         widgets = {
#             'move_in_date': forms.DateInput(attrs={'type': 'date'}),
#             'move_out_date': forms.DateInput(attrs={'type': 'date'}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
        
#         if user:
#             # Filter properties to only those owned by the user
#             self.fields['property'].queryset = Property.objects.filter(owner=user)
            
#             # Filter units to only those from user's properties
#             self.fields['unit'].queryset = Unit.objects.filter(property__owner=user, is_occupied=False)

from django import forms
from django.utils import timezone
from .models import Payment, MaintenanceRequest

class PaymentForm(forms.ModelForm):
    status = forms.ChoiceField(choices=Payment.PAYMENT_STATUS, required=True)
    payment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    
    class Meta:
        model = Payment
        fields = ['tenant', 'property', 'amount', 'payment_date', 'due_date', 
                  'payment_method', 'status', 'reference_number', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['tenant'].queryset = Tenant.objects.filter(property__owner=self.user)
            self.fields['property'].queryset = Property.objects.filter(owner=self.user)
        
        # Set default dates
        today = timezone.now().date()
        if not self.instance.pk:
            self.fields['payment_date'].initial = today
            self.fields['due_date'].initial = today + timezone.timedelta(days=30)
        
        # Add placeholders and help text
        self.fields['amount'].widget.attrs['placeholder'] = '0.00'
        self.fields['reference_number'].widget.attrs['placeholder'] = 'e.g., INV-001, MPESA-12345'
        self.fields['notes'].widget.attrs['placeholder'] = 'Any additional notes about this payment...'
        
        # Add CSS classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-input'
        
        # Add help text
        self.fields['reference_number'].help_text = 'Optional - receipt number, transaction ID, etc.'
        self.fields['notes'].help_text = 'Optional - additional information about this payment'
    
    def clean(self):
        cleaned_data = super().clean()
        payment_date = cleaned_data.get('payment_date')
        due_date = cleaned_data.get('due_date')
        amount = cleaned_data.get('amount')
        
        # Validate date logic
        if payment_date and due_date:
            if payment_date > timezone.now().date():
                raise forms.ValidationError({
                    'payment_date': 'Tarehe ya malipo haiwezi kuwa siku zijazo.'
                })
            
            if due_date < payment_date:
                raise forms.ValidationError({
                    'due_date': 'Tarehe ya malipo yawezi kuwa kabla ya tarehe ya malipo.'
                })
        
        # Validate amount
        if amount and amount <= 0:
            raise forms.ValidationError({
                'amount': 'Kiasi cha malipo lazima kiwe chanya.'
            })
        
        # Ensure tenant belongs to selected property
        tenant = cleaned_data.get('tenant')
        property_obj = cleaned_data.get('property')
        
        if tenant and property_obj and tenant.property != property_obj:
            raise forms.ValidationError({
                'tenant': 'Mpangaji huyu haishi katika mali iliyochaguliwa.'
            })
        
        return cleaned_data


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['property', 'unit', 'tenant', 'title', 'description', 'priority', 'status', 'cost']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe the issue in detail...'}),
            'cost': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter properties to only those owned by the user
            self.fields['property'].queryset = Property.objects.filter(owner=self.user)
            
            # For new requests, show only unassigned units by default
            # For editing, show all units from the selected property
            if self.instance and self.instance.pk and self.instance.property:
                self.fields['unit'].queryset = Unit.objects.filter(property=self.instance.property)
                self.fields['tenant'].queryset = Tenant.objects.filter(property=self.instance.property)
            else:
                self.fields['unit'].queryset = Unit.objects.none()
                self.fields['tenant'].queryset = Tenant.objects.none()
        
        # Add placeholders and help text
        self.fields['title'].widget.attrs['placeholder'] = 'e.g., Leaking faucet in kitchen'
        self.fields['cost'].help_text = 'Leave empty if cost is not known yet'
        
        # Add CSS classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-input'
    
    def clean(self):
        cleaned_data = super().clean()
        property_obj = cleaned_data.get('property')
        unit = cleaned_data.get('unit')
        tenant = cleaned_data.get('tenant')
        
        # Ensure unit belongs to selected property
        if property_obj and unit:
            if unit.property != property_obj:
                raise forms.ValidationError({
                    'unit': 'Selected unit does not belong to the selected property.'
                })
        
        # Ensure tenant belongs to selected property
        if property_obj and tenant:
            if tenant.property != property_obj:
                raise forms.ValidationError({
                    'tenant': 'Selected tenant does not belong to the selected property.'
                })
        
        # If tenant is selected, ensure they are in the selected unit
        if unit and tenant and tenant.unit != unit:
            raise forms.ValidationError({
                'tenant': 'Selected tenant is not assigned to the selected unit.'
            })
        
        return cleaned_data