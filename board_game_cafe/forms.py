from django import forms
from .models import Customer


passwordInputWidget = {
    'password': forms.PasswordInput(),
}


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'contact', 'password']
        widgets = [passwordInputWidget]


class LoginForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'password']
        widgets = [passwordInputWidget]