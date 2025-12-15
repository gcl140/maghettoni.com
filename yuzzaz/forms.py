import re
from django import forms
from .models import CustomUser
# from random_username.generate import generate_username

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jina la kwanza'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jina la mwisho'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Barua pepe'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nambari ya simu'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match!")
        return password2


    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.username = self.cleaned_data["telephone"]  # Set the username to telephone
        if commit:
            user.save()
        return user



class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-field',
                'placeholder': 'Email'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': '',
                'id': 'profile-picture-input'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user