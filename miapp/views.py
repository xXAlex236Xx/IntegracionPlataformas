from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from transbank.webpay.webpay_plus.transaction import Transaction
import random
from django.urls import reverse
import uuid
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Producto, Categoria, Sucursal, Stock, Pedido, Contacto, Cart, CartItem, DetallePedido
from .serializers import ProductoSerializer, CategoriaSerializer, StockSerializer, PedidoSerializer, ContactoSerializer
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegistroForm, LoginForm, ProductoForm, CategoriaForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import F
from django.conf import settings

def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        if created and request.session.get('session_cart_key'):
            try:
                anonymous_cart = Cart.objects.get(session_key=request.session['session_cart_key'])
                for item in anonymous_cart.items.all():
                    existing_item = cart.items.filter(producto=item.producto).first()
                    if existing_item:
                        existing_item.quantity = F('quantity') + item.quantity
                        existing_item.save()
                    else:
                        item.cart = cart
                        item.save()
                anonymous_cart.delete()
                del request.session['session_cart_key']
            except Cart.DoesNotExist:
                pass
        elif not created and request.session.get('session_cart_key'):
            try:
                anonymous_cart = Cart.objects.get(session_key=request.session['session_cart_key'])
                for item in anonymous_cart.items.all():
                    existing_item = cart.items.filter(producto=item.producto).first()
                    if existing_item:
                        existing_item.quantity = F('quantity') + item.quantity
                        existing_item.save()
                    else:
                        item.cart = cart
                        item.save()
                anonymous_cart.delete()
                del request.session['session_cart_key']
            except Cart.DoesNotExist:
                pass
        return cart
    else:
        session_cart_key = request.session.get('session_cart_key')
        if not session_cart_key:
            request.session.save()
            session_cart_key = request.session.session_key
            request.session['session_cart_key'] = session_cart_key

        cart, created = Cart.objects.get_or_create(session_key=session_cart_key)
        return cart

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
        return Response({'error': 'Faltan datos.'}, status=status.HTTP_400_BAD_REQUEST)

    pedido = Pedido.objects.create(sucursal_id=sucursal_id)

    for item in productos:
        try:
            producto = Producto.objects.get(codigo=item['codigo'])
            cantidad = item['cantidad']
            pedido.detallepedido_set.create(producto=producto, cantidad=cantidad, precio_unitario=producto.precio)
        except Producto.DoesNotExist:
            pedido.delete()
            return Response({'error': f"Producto {item['codigo']} no encontrado."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = PedidoSerializer(pedido)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def contacto(request):
    serializer = ContactoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            codigo_admin = form.cleaned_data.get('codigo_admin', '')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                
                if codigo_admin == 'ADMIN123':
                    user.is_staff = True
                    user.save()
                    messages.success(request, 'Usuario administrador creado exitosamente. ¡Inicia sesión!')
                    return redirect('login')
                elif not codigo_admin:
                    messages.success(request, 'Usuario registrado exitosamente. ¡Inicia sesión!')
                    return redirect('login')
                else:
                    user.delete()
                    messages.error(request, 'Código de administrador incorrecto. Inténtalo de nuevo o regístrate como usuario normal.')
                    return redirect('registro')
        else:
            messages.error(request, 'Hubo errores en el formulario. Por favor, corrígelos.')
    else:
        form = RegistroForm()
    
    return render(request, 'miapp/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido de nuevo, {user.username}!')
            if user.is_staff:
                return redirect('crud_admin')
            else:
                return redirect('inicio')
        else:
            messages.error(request, 'Credenciales incorrectas. Verifica tu usuario y contraseña.')
    else:
        form = LoginForm()
    return render(request, 'miapp/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

@user_passes_test(lambda u: u.is_staff)
@login_required
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
        messages.error(request, "No puedes eliminar tu propia cuenta desde aquí.")
        return redirect('crud_admin')

    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, f'El usuario "{user_to_delete.username}" ha sido eliminado permanentemente.')
        return redirect('crud_admin')
    
    messages.warning(request, "Operación no permitida por GET.")
    return redirect('crud_admin')

def producto_detail(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)

    clp_to_usd_rate = get_exchange_rate(base_currency='USD', target_currency='CLP')
    
    context = {
        'producto': producto,
        'clp_to_usd_rate': clp_to_usd_rate,
    }
    return render(request, 'miapp/producto_detail.html', context)

@user_passes_test(lambda u: u.is_staff)
@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{form.cleaned_data["nombre"]}" creado exitosamente.')
            return redirect('producto_list')
        else:
            messages.error(request, 'Hubo un error al crear el producto. Por favor, verifica los datos.')
    else:
        form = ProductoForm()
    context = {'form': form, 'form_title': 'Crear Nuevo Producto'}
    return render(request, 'miapp/producto_form.html', context)

@user_passes_test(lambda u: u.is_staff)
@login_required
def producto_update(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('producto_list')
        else:
            messages.error(request, 'Hubo un error al actualizar el producto. Por favor, verifica los datos.')
    else:
        form = ProductoForm(instance=producto)
    context = {'form': form, 'form_title': f'Actualizar Producto: {producto.nombre}'}
    return render(request, 'miapp/producto_form.html', context)

@user_passes_test(lambda u: u.is_staff)
@login_required
def producto_delete(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    if request.method == 'POST':
        if producto.imagen:
            producto.imagen.delete(save=False)
        producto.delete()
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        return redirect('producto_list')
    context = {'producto': producto}
    return render(request, 'miapp/producto_confirm_delete.html', context)

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_list(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'miapp/categoria_list.html', {'categorias': categorias})

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{form.cleaned_data["nombre"]}" creada exitosamente.')
            return redirect('categoria_list')
        else:
            messages.error(request, 'Hubo un error al crear la categoría. Por favor, verifica los datos.')
    else:
        form = CategoriaForm()
    return render(request, 'miapp/categoria_form.html', {'form': form, 'form_title': 'Crear Nueva Categoría'})

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            return redirect('categoria_list')
        else:
            messages.error(request, 'Hubo un error al actualizar la categoría. Por favor, verifica los datos.')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'miapp/categoria_form.html', {'form': form, 'form_title': f'Actualizar Categoría: {categoria.nombre}'})

@user_passes_test(lambda u: u.is_staff)
@login_required
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        if categoria.imagen:
            categoria.imagen.delete(save=False)
        categoria.delete()
        messages.success(request, f'Categoría "{categoria.nombre}" eliminada exitosamente.')
        return redirect('categoria_list')
    return render(request, 'miapp/categoria_confirm_delete.html', {'categoria': categoria})

@api_view(['POST'])
def add_to_cart(request):
    product_code = request.data.get('codigo')
    quantity = int(request.data.get('quantity', 1))

    if not product_code:
        return Response({'error': 'Se requiere el código del producto.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if quantity <= 0:
        return Response({'error': 'La cantidad debe ser un número positivo.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        producto = Producto.objects.get(codigo=product_code)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if producto.stock < quantity:
        messages.error(request, f'No hay suficiente stock para "{producto.nombre}". Stock disponible: {producto.stock}.')
        return Response({'error': 'No hay suficiente stock disponible.'}, status=status.HTTP_400_BAD_REQUEST)

    cart = _get_or_create_cart(request)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        producto=producto,
        defaults={'quantity': quantity}
    )

    if not created:
        if cart_item.quantity + quantity > producto.stock:
            messages.error(request, f'No puedes añadir más de {producto.stock} unidades de "{producto.nombre}" en total (ya tienes {cart_item.quantity}).')
            return Response({'error': 'Añadir esta cantidad excedería el stock disponible.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = F('quantity') + quantity
        cart_item.save()
        cart_item.refresh_from_db()
        messages.success(request, f'Cantidad de "{producto.nombre}" actualizada a {cart_item.quantity} en el carrito.')
    else:
        messages.success(request, f'"{producto.nombre}" añadido al carrito.')
    
    producto.stock -= quantity
    producto.save()
    
    return Response({'message': 'Producto añadido al carrito exitosamente.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def remove_from_cart(request):
    cart_item_id = request.data.get('cart_item_id')

    if not cart_item_id:
        return Response({'error': 'Se requiere el ID del artículo del carrito.'}, status=status.HTTP_400_BAD_REQUEST)

    cart = _get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        product_name = cart_item.producto.nombre
        cart_item.delete()
        messages.info(request, f'"{product_name}" eliminado del carrito.')
        return Response({'message': 'Producto eliminado del carrito exitosamente.'}, status=status.HTTP_200_OK)
    except CartItem.DoesNotExist:
        return Response({'error': 'El artículo del carrito no fue encontrado en tu carrito.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def update_cart_item_quantity(request):
    cart_item_id = request.data.get('cart_item_id')
    new_quantity = int(request.data.get('quantity', 0))

    if not cart_item_id or new_quantity < 0:
        return Response({'error': 'Se requiere el ID del artículo del carrito y una cantidad no negativa.'}, status=status.HTTP_400_BAD_REQUEST)

    cart = _get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        
        if new_quantity > cart_item.producto.stock:
            messages.error(request, f'No puedes cambiar la cantidad de "{cart_item.producto.nombre}" a {new_quantity}. Stock disponible: {cart_item.producto.stock}.')
            return Response({'error': 'La cantidad excede el stock disponible.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_quantity == 0:
            product_name = cart_item.producto.nombre
            cart_item.delete()
            messages.info(request, f'"{product_name}" eliminado del carrito.')
            return Response({'message': 'Producto eliminado del carrito (cantidad establecida en 0).'}, status=status.HTTP_200_OK)
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f'Cantidad de "{cart_item.producto.nombre}" actualizada a {new_quantity}.')
            return Response({'message': 'Cantidad del artículo del carrito actualizada exitosamente.'}, status=status.HTTP_200_OK)
    except CartItem.DoesNotExist:
        return Response({'error': 'El artículo del carrito no fue encontrado en tu carrito.'}, status=status.HTTP_404_NOT_FOUND)

def view_cart(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.all()
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'miapp/cart.html', context)

def iniciar_pago_webpay(request):
    cart = _get_or_create_cart(request)
    amount = cart.get_total_price()

    if amount <= 0:
        messages.error(request, 'El monto del carrito debe ser mayor a cero para iniciar el pago.')
        return redirect('view_cart')

    buy_order = str(random.randrange(1000000, 999999999))
    session_id = str(uuid.uuid4())[:20]

    return_url = request.build_absolute_uri(reverse('confirmar_pago_webpay'))

    try:
        Transaction.commerce_code = settings.WEBPAY_PLUS_COMMERCE_CODE
        Transaction.api_key = settings.WEBPAY_PLUS_API_KEY
        Transaction.environment = settings.WEBPAY_PLUS_ENVIRONMENT
        
        response = Transaction.create(buy_order, session_id, amount, return_url)

        url = response['url']
        token = response['token']

        request.session['webpay_token'] = token
        request.session['webpay_buy_order'] = buy_order
        request.session['webpay_amount'] = str(amount)

        return render(request, 'miapp/webpay_redirect.html', {'url': url, 'token': token})

    except Exception as e:
        print(f"Error al iniciar transacción Webpay: {e}")
        messages.error(request, f'Error al iniciar el pago con Webpay: {e}. Por favor, inténtalo de nuevo.')
        return redirect('view_cart')


def confirmar_pago_webpay(request):
    token = request.POST.get('token_ws') or request.GET.get('token_ws')
    tbk_token = request.POST.get('TBK_TOKEN') or request.GET.get('TBK_TOKEN')

    if tbk_token:
        messages.warning(request, 'El pago fue anulado por el usuario en el sitio de WebPay.')
        if 'webpay_token' in request.session:
            del request.session['webpay_token']
        if 'webpay_buy_order' in request.session:
            del request.session['webpay_buy_order']
        if 'webpay_amount' in request.session:
            del request.session['webpay_amount']
        return render(request, 'miapp/pago_resultado.html', {'status': 'anulado', 'message': 'El pago fue anulado por el usuario.'})

    if not token:
        messages.error(request, 'No se recibió el token de Webpay para confirmar el pago.')
        return render(request, 'miapp/pago_resultado.html', {'status': 'error', 'message': 'No se recibió el token de Webpay para confirmar el pago.'})

    Transaction.commerce_code = settings.WEBPAY_PLUS_COMMERCE_CODE
    Transaction.api_key = settings.WEBPAY_PLUS_API_KEY
    Transaction.environment = settings.WEBPAY_PLUS_ENVIRONMENT

    try:
        response = Transaction.commit(token)

        if response and response.get('response_code') == 0:
            status_pago = 'aprobado'
            message = f"¡Pago aprobado! Tu transacción fue exitosa. Código de Autorización: {response.get('authorization_code')}, Últimos 4 dígitos de tarjeta: {response.get('card_number')[-4:]}."
            
            cart = _get_or_create_cart(request)
            
            try:
                sucursal_default = Sucursal.objects.first() 
                if not sucursal_default:
                    raise Exception("Error: No hay sucursales configuradas en la base de datos para crear el pedido. Por favor, crea al menos una desde el panel de administración.")

                pedido = Pedido.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    sucursal=sucursal_default,
                    fecha_creacion=response.get('transaction_date'),
                    completado=True,
                )

                for item in cart.items.all():
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=item.producto,
                        cantidad=item.quantity,
                        precio_unitario=item.producto.precio
                    )
                    item.producto.stock -= item.quantity
                    item.producto.save()
                
                messages.success(request, f'Tu pedido (ID: {pedido.id}) ha sido creado exitosamente y el pago aprobado.')

                cart.items.all().delete()
                
                if 'webpay_token' in request.session:
                    del request.session['webpay_token']
                if 'webpay_buy_order' in request.session:
                    del request.session['webpay_buy_order']
                if 'webpay_amount' in request.session:
                    del request.session['webpay_amount']

            except Exception as db_error:
                print(f"Error al procesar el pedido después de pago exitoso: {db_error}")
                messages.error(request, f'Pago aprobado, pero hubo un error al procesar tu pedido: {db_error}. Contacta a soporte y proporciona el ID de transacción.')
                status_pago = 'error'
                message += f" (Error interno al procesar el pedido: {db_error})"

        else:
            status_pago = 'rechazado'
            error_message_webpay = response.get('response_code', 'N/A')
            messages.error(request, f"El pago ha sido rechazado. Código de respuesta: {error_message_webpay}. Por favor, verifica tus datos o intenta con otro método de pago.")
            message = f"El pago ha sido rechazado. Código de respuesta: {error_message_webpay}. Por favor, verifica tus datos o intenta con otro método de pago."

        return render(request, 'miapp/pago_resultado.html', {'status': status_pago, 'response': response, 'message': message})

    except Exception as e:
        print(f"Error al confirmar transacción Webpay: {e}")
        messages.error(request, f'Error interno al procesar la confirmación del pago: {e}')
        return render(request, 'miapp/pago_resultado.html', {'status': 'error', 'message': f'Error interno al procesar la confirmación del pago: {e}'})
    
def get_exchange_rate(base_currency='USD', target_currency='CLP'):
    api_key = settings.EXCHANGE_RATE_API_KEY

    if not api_key:
        print("ERROR: La clave API (EXCHANGE_RATE_API_KEY) no está configurada en settings.py. No se puede obtener la tasa de cambio.")
        return None

    API_URL = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get('result') == 'success' and 'conversion_rates' in data and target_currency in data['conversion_rates']:
            usd_to_clp_rate = data['conversion_rates'][target_currency]
            if usd_to_clp_rate > 0:
                return 1 / usd_to_clp_rate 
            else:
                print(f"Error: La tasa de cambio de {target_currency} para {base_currency} es cero o inválida.")
                return None
        else:
            error_type = data.get('error-type', 'desconocido')
            print(f"Error en la respuesta de la API de tasa de cambio: {error_type}. Respuesta completa: {data}")
            return None

    except requests.exceptions.Timeout:
        print("Error: La solicitud a la API de tasa de cambio excedió el tiempo de espera.")
        return None
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar a la API de tasa de cambio. Verifica tu conexión a internet.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error general de solicitud HTTP a la API de tasa de cambio: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al procesar la tasa de cambio: {e}")
        return None

def producto_list(request):

    categorias = Categoria.objects.all().order_by('nombre')

    categorias_con_productos = []
    for categoria in categorias:
        productos_en_categoria = Producto.objects.filter(categoria=categoria).order_by('nombre')
        categorias_con_productos.append({
            'categoria': categoria,
            'productos': productos_en_categoria
        })
    
    productos_sin_categoria = Producto.objects.filter(categoria__isnull=True).order_by('nombre')
    if productos_sin_categoria.exists():
        categorias_con_productos.append({
            'categoria': {'nombre': 'Sin Categoría', 'id': 'no-category'},
            'productos': productos_sin_categoria
        })

    clp_to_usd_rate = get_exchange_rate(base_currency='USD', target_currency='CLP')
    
    context = {
        'categorias_con_productos': categorias_con_productos,
        'clp_to_usd_rate': clp_to_usd_rate,
    }
    return render(request, 'miapp/producto_list.html', context)