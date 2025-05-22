# miapp/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Producto, Categoria

class RegistroForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}))
    codigo_admin = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código de administrador (opcional)'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio', 'stock', 'imagen']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'imagen'] # Added 'imagen'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }