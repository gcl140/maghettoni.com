from django import forms
from dashboardd.models import Tenant


_input = 'w-full bg-brown-700 border border-brown-600 border-l-4 border-l-amber-500 text-white px-4 py-3 focus:outline-none focus:ring-0 focus:border-l-amber-400 placeholder-brown-400'
_textarea = _input + ' resize-none'


_tp_input = 'w-full bg-white border border-gray-200 border-l-4 border-l-amber-500 py-2.5 px-3 text-gray-900 focus:outline-none focus:ring-0 focus:border-l-amber-600 placeholder-gray-400'


class TenantProfileEditForm(forms.ModelForm):
    preferred_language = forms.ChoiceField(
        choices=[('en', 'EN'), ('sw', 'SW')],
        required=False,
        widget=forms.RadioSelect(),
    )

    class Meta:
        model = Tenant
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'emergency_contact', 'emergency_phone',
            'notes', 'profile_picture',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': _tp_input, 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': _tp_input, 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': _tp_input, 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': _tp_input, 'placeholder': '+255 7XX XXX XXX'}),
            'emergency_contact': forms.TextInput(attrs={'class': _tp_input, 'placeholder': 'Emergency contact name'}),
            'emergency_phone': forms.TextInput(attrs={'class': _tp_input, 'placeholder': '+255 7XX XXX XXX'}),
            'notes': forms.Textarea(attrs={'class': _tp_input + ' resize-none', 'rows': 3, 'placeholder': 'Anything the landlord should know...'}),
            'profile_picture': forms.FileInput(attrs={'id': 'profile-picture-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if user:
            self.fields['preferred_language'].initial = user.preferred_language or 'en'

    def save(self, commit=True):
        tenant = super().save(commit=commit)
        if commit and self._user:
            lang = self.cleaned_data.get('preferred_language', 'en')
            if lang in ('en', 'sw'):
                self._user.preferred_language = lang
            self._user.first_name = tenant.first_name
            self._user.last_name = tenant.last_name
            self._user.save(update_fields=['preferred_language', 'first_name', 'last_name'])
        return tenant


class TenantPaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money (M-Pesa / Tigo / Airtel)'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash Deposit'),
    ]

    amount = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': _input,
            'placeholder': '0.00',
            'min': '1',
            'step': '0.01',
        })
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': _input})
    )
    phone_number = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': _input,
            'placeholder': '+255 7XX XXX XXX',
        })
    )
    reference = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': _input,
            'placeholder': 'Reference number (optional)',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': _textarea,
            'rows': 3,
            'placeholder': 'Additional notes...',
        })
    )

    def __init__(self, *args, unit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._unit = unit
        if unit and unit.min_rental_months > 1:
            minimum = unit.monthly_rent * unit.min_rental_months
            self.fields['amount'].widget.attrs['min'] = str(minimum)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        if amount > 10_000_000:
            raise forms.ValidationError('Amount is too large. Please contact your landlord.')
        if self._unit and self._unit.min_rental_months > 1:
            minimum = self._unit.monthly_rent * self._unit.min_rental_months
            if amount < minimum:
                raise forms.ValidationError(
                    f'This unit requires a minimum payment of TZS. {minimum:,.0f} '
                    f'({self._unit.min_rental_months} months × TZS. {self._unit.monthly_rent:,.0f}/mo). '
                    f'Please enter at least that amount.'
                )
        return amount

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        phone = cleaned.get('phone_number', '').strip()
        if method == 'mobile_money' and not phone:
            self.add_error('phone_number', 'Phone number is required for mobile money payments.')
        return cleaned


class TenantMaintenanceForm(forms.Form):
    PRIORITY_CHOICES = [
        ('low', 'Low — Not Urgent'),
        ('medium', 'Medium — Standard'),
        ('high', 'High — Urgent'),
        ('emergency', 'Emergency — Immediately!'),
    ]

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': _input,
            'placeholder': 'e.g. Broken water pipe in bathroom',
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': _textarea,
            'rows': 5,
            'placeholder': 'Describe the issue in detail...',
        })
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': _input})
    )
