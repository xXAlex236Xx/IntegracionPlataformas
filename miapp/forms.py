from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

class RegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    codigo_admin = forms.CharField(required=False, help_text="Código para ser administrador (opcional)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'codigo_admin']

class LoginForm(AuthenticationForm):
    # AuthenticationForm ya incluye username y password
    # Puedes personalizar aquí si necesitas campos adicionales, pero para lo básico no es necesario redeclararlos
    pass