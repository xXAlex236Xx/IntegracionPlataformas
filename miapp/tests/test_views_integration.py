# miapp/tests/test_views_integration.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from miapp.models import Producto, Categoria, Cart, CartItem
import unittest.mock as mock
from django.conf import settings
from decimal import Decimal

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def categoria_fixture():
    return Categoria.objects.create(nombre="Electrónica")

@pytest.fixture
def test_user():
    user, created = User.objects.get_or_create(username='testuser', defaults={'password': 'testpassword'})
    return user

@pytest.fixture
def staff_user():
    user, created = User.objects.get_or_create(username='staffuser', defaults={'password': 'staffpassword', 'is_staff': True})
    return user

@pytest.fixture
def producto_con_stock(categoria_fixture):
    return Producto.objects.create(
        codigo='PROD_STOCK_OK',
        nombre='Laptop',
        precio=Decimal('1000.00'),
        stock=10,
        categoria=categoria_fixture
    )

@pytest.fixture
def producto_sin_stock(categoria_fixture):
    return Producto.objects.create(
        codigo='PROD_SIN_STOCK',
        nombre='Mouse Pad',
        precio=5.00,
        stock=0,
        categoria=categoria_fixture
    )

@pytest.mark.django_db
def test_add_to_cart_reduces_product_stock_and_adds_item(api_client, producto_con_stock, test_user):
    api_client.force_authenticate(user=test_user)
    initial_stock = producto_con_stock.stock
    quantity_to_add = 3
    url = reverse('add_to_cart')

    response = api_client.post(url, {'codigo': producto_con_stock.codigo, 'quantity': quantity_to_add}, format='json')

    assert response.status_code == 200
    assert 'Producto añadido al carrito exitosamente.' in response.data['message']

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == initial_stock - quantity_to_add

    cart = Cart.objects.get(user=test_user)
    cart_item = CartItem.objects.get(cart=cart, producto=producto_con_stock)
    assert cart_item.quantity == quantity_to_add

@pytest.mark.django_db
def test_add_to_cart_fails_if_no_stock(api_client, producto_sin_stock, test_user):
    api_client.force_authenticate(user=test_user)
    url = reverse('add_to_cart')

    response = api_client.post(url, {'codigo': producto_sin_stock.codigo, 'quantity': 1}, format='json')
    
    assert response.status_code == 400
    assert 'No hay suficiente stock disponible.' in response.data['error']
    producto_sin_stock.refresh_from_db()
    assert producto_sin_stock.stock == 0
    assert not CartItem.objects.filter(producto=producto_sin_stock).exists()


@pytest.mark.django_db
def test_add_to_cart_fails_if_quantity_exceeds_stock(api_client, producto_con_stock, test_user):
    api_client.force_authenticate(user=test_user)
    url = reverse('add_to_cart')

    response = api_client.post(url, {'codigo': producto_con_stock.codigo, 'quantity': producto_con_stock.stock + 1}, format='json')
    
    assert response.status_code == 400
    assert 'No hay suficiente stock disponible.' in response.data['error']
    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10
    assert not CartItem.objects.filter(producto=producto_con_stock).exists()

@pytest.mark.django_db
def test_non_staff_cannot_create_product(client, test_user, categoria_fixture):
    client.login(username=test_user.username, password='testpassword')
    url = reverse('producto_create')

    response = client.get(url)
    assert response.status_code == 302
    assert 'login' in response.url

@pytest.mark.django_db
def test_staff_can_create_product(admin_client, categoria_fixture):
    url = reverse('producto_create')

    response = admin_client.get(url)
    assert response.status_code == 200
    assert 'Crear Nuevo Producto' in response.content.decode('utf-8')

@pytest.mark.django_db
def test_producto_list_displays_prices_in_usd_and_clp(client, producto_con_stock, categoria_fixture):
    url = reverse('producto_list')
    with mock.patch('miapp.views.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'result': 'success',
            'conversion_rates': {'CLP': 900.0}
        }
        mock_get.return_value.raise_for_status.return_value = None

        response = client.get(url)
        content = response.content.decode('utf-8')

        assert response.status_code == 200
        
        clp_price_str = f"${producto_con_stock.precio.quantize(Decimal('1')).to_integral_value()} CLP"
        assert clp_price_str in content

        expected_usd_price = (producto_con_stock.precio / Decimal('900.0')).quantize(Decimal('0.01'))
        usd_price_str = f"≈ ${expected_usd_price} USD"
        assert usd_price_str in content

        mock_get.assert_called_once_with(
            f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/USD", timeout=5
        )

@pytest.mark.django_db
def test_remove_from_cart(api_client, producto_con_stock, test_user):
    api_client.force_authenticate(user=test_user)
    cart = Cart.objects.create(user=test_user)
    cart_item = CartItem.objects.create(cart=cart, producto=producto_con_stock, quantity=2)

    url = reverse('remove_from_cart')
    response = api_client.post(url, {'cart_item_id': cart_item.id}, format='json')

    assert response.status_code == 200
    assert 'Producto eliminado del carrito exitosamente.' in response.data['message']
    assert not CartItem.objects.filter(id=cart_item.id).exists()

@pytest.mark.django_db
def test_update_cart_item_quantity(api_client, producto_con_stock, test_user):
    api_client.force_authenticate(user=test_user)
    cart = Cart.objects.create(user=test_user)
    cart_item = CartItem.objects.create(cart=cart, producto=producto_con_stock, quantity=2)

    url = reverse('update_cart_item_quantity')
    new_quantity = 5
    response = api_client.post(url, {'cart_item_id': cart_item.id, 'quantity': new_quantity}, format='json')

    assert response.status_code == 200
    cart_item.refresh_from_db()
    assert cart_item.quantity == new_quantity
    assert 'Cantidad del artículo del carrito actualizada exitosamente.' in response.data['message']

@pytest.mark.django_db
def test_update_cart_item_quantity_to_zero_removes_item(api_client, producto_con_stock, test_user):
    api_client.force_authenticate(user=test_user)
    cart = Cart.objects.create(user=test_user)
    cart_item = CartItem.objects.create(cart=cart, producto=producto_con_stock, quantity=2)

    url = reverse('update_cart_item_quantity')
    response = api_client.post(url, {'cart_item_id': cart_item.id, 'quantity': 0}, format='json')

    assert response.status_code == 200
    assert 'Producto eliminado del carrito (cantidad establecida en 0).' in response.data['message']
    assert not CartItem.objects.filter(id=cart_item.id).exists()