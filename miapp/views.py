from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Producto, Categoria, Sucursal, Stock, Pedido, Contacto
from .serializers import ProductoSerializer, CategoriaSerializer, StockSerializer, PedidoSerializer, ContactoSerializer
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegistroForm, LoginForm
from django.contrib import messages
from django.contrib.auth.models import User

def inicio(request):
    return render(request, 'miapp/inicio.html')

class ProductoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    lookup_field = 'codigo'

class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

@api_view(['GET'])
def stock_por_sucursal(request, id):
    stock = Stock.objects.filter(sucursal_id=id)
    serializer = StockSerializer(stock, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def crear_pedido(request):
    sucursal_id = request.data.get('sucursal')
    productos = request.data.get('productos')

    if not sucursal_id or not productos:
        return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

    pedido = Pedido.objects.create(sucursal_id=sucursal_id)

    for item in productos:
        try:
            producto = Producto.objects.get(codigo=item['codigo'])
            cantidad = item['cantidad']
            pedido.detallepedido_set.create(producto=producto, cantidad=cantidad)
        except Producto.DoesNotExist:
            pedido.delete()
            return Response({'error': f"Producto {item['codigo']} no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = PedidoSerializer(pedido)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def contacto(request):
    serializer = ContactoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def convertir_moneda(request):
    monto = request.query_params.get('monto')
    de = request.query_params.get('de')
    a = request.query_params.get('a')

    if not monto or not de or not a:
        return Response({'error': 'Parámetros monto, de y a son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    url = f"https://api.bancocentral.example/convert?from={de}&to={a}&amount={monto}"

    try:
        r = requests.get(url)
        data = r.json()
        return Response(data)
    except Exception as e:
        return Response({'error': 'No se pudo conectar con la API del Banco Central'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            codigo_admin = form.cleaned_data.get('codigo_admin', '')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Nombre de usuario ya existe.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                
                if codigo_admin == 'ADMIN123':
                    user.is_staff = True
                    user.save()
                    messages.success(request, 'Usuario administrador creado exitosamente. Inicie sesión.')
                    return redirect('login')
                elif not codigo_admin:
                    messages.success(request, 'Usuario registrado exitosamente. Inicie sesión.')
                    return redirect('login')
                else:
                    user.delete()
                    messages.error(request, 'Código de administrador incorrecto. Inténtelo de nuevo o regístrese como usuario normal.')
                    return redirect('registro')
        else:
            messages.error(request, 'Hubo errores en el formulario. Por favor, corríjalos.')
    else:
        form = RegistroForm()
    
    return render(request, 'miapp/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido de nuevo, {user.username}!')
            return redirect('/')
        else:
            messages.error(request, 'Credenciales incorrectas. Verifique su usuario y contraseña.')
    else:
        form = LoginForm()
    return render(request, 'miapp/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard_view(request):
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()
    sucursales = Sucursal.objects.all()
    usuarios = User.objects.all().order_by('username')

    return render(request, 'miapp/crud_admin.html', {
        'productos': productos,
        'categorias': categorias,
        'sucursales': sucursales,
        'usuarios': usuarios,
    })

@user_passes_test(lambda u: u.is_staff)
@login_required
def borrar_usuario(request, user_id):
    user_to_delete = get_object_or_404(User, pk=user_id)
    
    # CRÍTICO: No permitir que un administrador se borre a sí mismo.
    if user_to_delete.id == request.user.id:
        messages.error(request, "No puedes borrar tu propia cuenta desde aquí.")
        return redirect('crud_admin')

    if request.method == 'POST':
        # Al borrar el usuario, el sistema de autenticación de Django
        # automáticamente invalida la sesión si el usuario borrado es el logeado.
        # Sin embargo, hemos puesto la restricción para que no se pueda borrar a sí mismo.
        # Si se llegara a borrar de alguna otra forma (ej: desde el admin de Django),
        # la sesión del usuario borrado se cerrará automáticamente.
        
        user_to_delete.delete()
        messages.success(request, f'El usuario "{user_to_delete.username}" ha sido borrado permanentemente.')
        
        # Como hemos bloqueado que se borre a sí mismo, siempre redirigimos al admin
        return redirect('crud_admin')
    
    messages.warning(request, "Operación no permitida por GET.")
    return redirect('crud_admin')