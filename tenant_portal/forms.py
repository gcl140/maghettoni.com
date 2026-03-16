from django import forms


_input = 'w-full bg-brown-700 border border-brown-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500 placeholder-brown-400'
_textarea = _input + ' resize-none'


class TenantPaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('mobile_money', 'M-Pesa / Tigo / Airtel Money'),
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
            'placeholder': 'Nambari ya rejeleo (hiari)',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': _textarea,
            'rows': 3,
            'placeholder': 'Maelezo ya ziada...',
        })
    )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Kiasi lazima kiwe zaidi ya sifuri.')
        if amount > 10_000_000:
            raise forms.ValidationError('Kiasi ni kikubwa mno. Wasiliana na msimamizi.')
        return amount

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        phone = cleaned.get('phone_number', '').strip()
        if method == 'mobile_money' and not phone:
            self.add_error('phone_number', 'Nambari ya simu inahitajika kwa malipo ya simu.')
        return cleaned


class TenantMaintenanceForm(forms.Form):
    PRIORITY_CHOICES = [
        ('low', 'Chini — Sio ya Haraka'),
        ('medium', 'Wastani — Kawaida'),
        ('high', 'Juu — Haraka'),
        ('emergency', 'Dharura — Mara Moja!'),
    ]

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': _input,
            'placeholder': 'Mfano: Bomba la maji limevunjika',
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': _textarea,
            'rows': 5,
            'placeholder': 'Elezea tatizo kwa undani zaidi...',
        })
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': _input})
    )
