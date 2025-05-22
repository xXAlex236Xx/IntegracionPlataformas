# miapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Producto, Categoria, Sucursal, Stock, Pedido, Contacto
from .serializers import ProductoSerializer, CategoriaSerializer, StockSerializer, PedidoSerializer, ContactoSerializer
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegistroForm, LoginForm, ProductoForm, CategoriaForm
from django.contrib import messages
from django.contrib.auth.models import User

def inicio(request):
    categorias = Categoria.objects.all().order_by('nombre')
    productos_destacados = Producto.objects.all().order_by('-precio')[:3]

    context = {
        'categorias': categorias,
        'productos_destacados': productos_destacados,
    }
    return render(request, 'miapp/inicio.html', context)

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
            # Pass precio_unitario to DetallePedido create to store the price at the time of order
            pedido.detallepedido_set.create(producto=producto, cantidad=cantidad, precio_unitario=producto.precio)
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
        r.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = r.json()
        return Response(data)
    except requests.exceptions.RequestException as e:
        # Handle specific request errors (e.g., connection issues, timeout)
        return Response({'error': f'Error al conectar con la API externa: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        # Catch any other unexpected errors
        return Response({'error': f'Ocurrió un error inesperado: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                
                if codigo_admin == 'ADMIN123': # Código de administrador
                    user.is_staff = True
                    user.save()
                    messages.success(request, 'Usuario administrador creado exitosamente. Inicie sesión.')
                    return redirect('login')
                elif not codigo_admin:
                    messages.success(request, 'Usuario registrado exitosamente. Inicie sesión.')
                    return redirect('login')
                else:
                    user.delete() # Elimina el usuario si el código es incorrecto
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
            if user.is_staff:
                return redirect('crud_admin')
            else:
                return redirect('inicio')
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
@login_required # Added login_required for admin_dashboard
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
    
    if user_to_delete.id == request.user.id:
        messages.error(request, "No puedes borrar tu propia cuenta desde aquí.")
        return redirect('crud_admin')

    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, f'El usuario "{user_to_delete.username}" ha sido borrado permanentemente.')
        return redirect('crud_admin')
    
    messages.warning(request, "Operación no permitida por GET.")
    return redirect('crud_admin')

# --- CRUD para Productos ---

# READ (Listar Productos)
def producto_list(request):
    productos = Producto.objects.all().order_by('nombre')
    context = {'productos': productos}
    return render(request, 'miapp/producto_list.html', context)

# READ (Detalle de un Producto)
def producto_detail(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    context = {'producto': producto}
    return render(request, 'miapp/producto_detail.html', context)

# CREATE (Crear un Producto) - AHORA MANEJA ARCHIVOS
@user_passes_test(lambda u: u.is_staff)
@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES) # <--- ADD request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{form.cleaned_data["nombre"]}" creado exitosamente.')
            return redirect('producto_list')
        else:
            messages.error(request, 'Hubo un error al crear el producto. Por favor, verifique los datos.')
    else:
        form = ProductoForm()
    context = {'form': form, 'form_title': 'Crear Nuevo Producto'}
    return render(request, 'miapp/producto_form.html', context)

# UPDATE (Actualizar un Producto) - AHORA MANEJA ARCHIVOS
@user_passes_test(lambda u: u.is_staff)
@login_required
def producto_update(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto) # <--- ADD request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('producto_list')
        else:
            messages.error(request, 'Hubo un error al actualizar el producto. Por favor, verifique los datos.')
    else:
        form = ProductoForm(instance=producto)
    context = {'form': form, 'form_title': f'Actualizar Producto: {producto.nombre}'}
    return render(request, 'miapp/producto_form.html', context)

# DELETE (Eliminar un Producto) - Added image deletion logic
@user_passes_test(lambda u: u.is_staff)
@login_required
def producto_delete(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    if request.method == 'POST':
        # Optional: Delete the image file from the filesystem when deleting the object
        if producto.imagen:
            producto.imagen.delete(save=False) # save=False prevents trying to save the object after deleting the image
        producto.delete()
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        return redirect('producto_list')
    context = {'producto': producto}
    return render(request, 'miapp/producto_confirm_delete.html', context)

# --- CRUD para Categorías ---

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_list(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'miapp/categoria_list.html', {'categorias': categorias})

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES) # <--- ADD request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{form.cleaned_data["nombre"]}" creada exitosamente.')
            return redirect('categoria_list')
        else:
            messages.error(request, 'Hubo un error al crear la categoría. Por favor, verifique los datos.')
    else:
        form = CategoriaForm()
    return render(request, 'miapp/categoria_form.html', {'form': form, 'form_title': 'Crear Nueva Categoría'})

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES, instance=categoria) # <--- ADD request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            return redirect('categoria_list')
        else:
            messages.error(request, 'Hubo un error al actualizar la categoría. Por favor, verifique los datos.')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'miapp/categoria_form.html', {'form': form, 'form_title': f'Actualizar Categoría: {categoria.nombre}'})

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        # Optional: Delete the image file from the filesystem when deleting the object
        if categoria.imagen:
            categoria.imagen.delete(save=False)
        categoria.delete()
        messages.success(request, f'Categoría "{categoria.nombre}" eliminada exitosamente.')
        return redirect('categoria_list')
    return render(request, 'miapp/categoria_confirm_delete.html', {'categoria': categoria})