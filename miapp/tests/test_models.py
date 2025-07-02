# miapp/tests/test_models.py
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from miapp.models import Producto, Categoria, Cart, CartItem
from django.contrib.auth.models import User
from django.conf import settings

@pytest.fixture
def categoria_fixture():
    return Categoria.objects.create(nombre="Electrónica")

@pytest.fixture
def test_user():
    user, created = User.objects.get_or_create(username='testuser', defaults={'password': 'testpassword'})
    return user

@pytest.mark.django_db
def test_producto_no_acepta_precio_negativo(categoria_fixture):
    """Verifica que la creación de un producto con precio negativo falle debido a validación."""
    with pytest.raises(ValidationError) as excinfo:
        producto = Producto(
            codigo='P001_NEG_PRECIO',
            nombre='Producto Precio Negativo',
            descripcion='Test',
            precio=-10.00,
            stock=10,
            categoria=categoria_fixture
        )
        producto.full_clean()

    assert 'precio' in excinfo.value.message_dict
    assert 'Ensure this value is greater than or equal to 0.0.' in excinfo.value.message_dict['precio'][0]

@pytest.mark.django_db
def test_producto_acepta_precio_cero(categoria_fixture):
    """Verifica que un producto pueda tener precio cero."""
    try:
        producto = Producto.objects.create(
            codigo='P002_PRECIO_CERO',
            nombre='Producto Gratis',
            descripcion='Test',
            precio=0.00,
            stock=10,
            categoria=categoria_fixture
        )
        assert producto.precio == 0.00
    except ValidationError:
        pytest.fail("La creación de producto con precio 0.00 no debería fallar.")

@pytest.mark.django_db
def test_producto_no_acepta_nombre_vacio(categoria_fixture):
    """Verifica que la creación de un producto con nombre vacío falle."""
    with pytest.raises(ValidationError) as excinfo:
        producto = Producto(
            codigo='P003_EMPTY_NAME',
            nombre='',
            descripcion='Test',
            precio=100.00,
            stock=5,
            categoria=categoria_fixture
        )
        producto.full_clean()

    assert 'nombre' in excinfo.value.message_dict
    assert 'This field cannot be blank.' in excinfo.value.message_dict['nombre'][0]

@pytest.mark.django_db
def test_producto_codigo_es_unico(categoria_fixture):
    """Verifica que no se pueda crear un producto con un código duplicado."""
    Producto.objects.create(
        codigo='CODIGOUNICO',
        nombre='Producto Original',
        precio=100.00,
        stock=5,
        categoria=categoria_fixture
    )
    
    with pytest.raises(IntegrityError):
        Producto.objects.create(
            codigo='CODIGOUNICO',
            nombre='Producto Duplicado',
            precio=200.00,
            stock=10,
            categoria=categoria_fixture
        )

@pytest.mark.django_db
def test_producto_no_acepta_stock_negativo(categoria_fixture):
    """Verifica que la creación de un producto con stock negativo falle debido a validación."""
    with pytest.raises(ValidationError) as excinfo:
        producto = Producto(
            codigo='P004_NEG_STOCK',
            nombre='Producto Stock Negativo',
            descripcion='Test',
            precio=50.00,
            stock=-5,
            categoria=categoria_fixture
        )
        producto.full_clean()

    assert 'stock' in excinfo.value.message_dict
    assert 'Ensure this value is greater than or equal to 0.' in excinfo.value.message_dict['stock'][0]

@pytest.mark.django_db
def test_producto_acepta_stock_cero(categoria_fixture):
    """Verifica que un producto pueda tener stock cero."""
    try:
        producto = Producto.objects.create(
            codigo='P005_STOCK_CERO',
            nombre='Producto Stock Cero',
            descripcion='Test',
            precio=50.00,
            stock=0,
            categoria=categoria_fixture
        )
        assert producto.stock == 0
    except ValidationError:
        pytest.fail("La creación de producto con stock 0 no debería fallar.")

from miapp.templatetags.custom_filters import div, mul

def test_custom_filter_div_correct_division():
    """Verifica que el filtro 'div' realiza una división correcta."""
    assert div(10, 2) == 5.0
    assert div(7, 2) == 3.5

def test_custom_filter_div_by_zero():
    """Verifica que el filtro 'div' maneja la división por cero."""
    assert div(10, 0) is None

def test_custom_filter_div_invalid_input():
    """Verifica que el filtro 'div' maneja entradas no numéricas."""
    assert div("abc", 2) is None
    assert div(10, "xyz") is None

def test_custom_filter_mul_correct_multiplication():
    """Verifica que el filtro 'mul' realiza una multiplicación correcta."""
    assert mul(10, 2) == 20.0
    assert mul(7, 2.5) == 17.5

def test_custom_filter_mul_invalid_input():
    """Verifica que el filtro 'mul' maneja entradas no numéricas."""
    assert mul("abc", 2) is None
    assert mul(10, "xyz") is None