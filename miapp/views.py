from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Producto, Categoria, Sucursal, Stock, Pedido, Contacto
from .serializers import ProductoSerializer, CategoriaSerializer, StockSerializer, PedidoSerializer, ContactoSerializer
import requests

# Create your views here.
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
    # Esperamos JSON con sucursal y lista de productos con cantidad
    sucursal_id = request.data.get('sucursal')
    productos = request.data.get('productos')  # [{codigo: X, cantidad: Y}, ...]

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
    # Parámetros esperados: ?monto=100&de=USD&a=UYU (ejemplo)
    monto = request.query_params.get('monto')
    de = request.query_params.get('de')
    a = request.query_params.get('a')

    if not monto or not de or not a:
        return Response({'error': 'Parámetros monto, de y a son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    # Aquí se llama a la API del Banco Central (ejemplo ficticio, reemplazar URL y lógica)
    url = f"https://api.bancocentral.example/convert?from={de}&to={a}&amount={monto}"

    try:
        r = requests.get(url)
        data = r.json()
        return Response(data)
    except Exception as e:
        return Response({'error': 'No se pudo conectar con la API del Banco Central'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
