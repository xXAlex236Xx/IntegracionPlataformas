from rest_framework import serializers
from .models import Categoria, Producto, Sucursal, Stock, Pedido, DetallePedido, Contacto

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']

class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio']

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'direccion']

class StockSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    class Meta:
        model = Stock
        fields = ['producto', 'cantidad']

class DetallePedidoSerializer(serializers.ModelSerializer):
    producto = serializers.CharField(source='producto.codigo')
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad']

class PedidoSerializer(serializers.ModelSerializer):
    detalle = DetallePedidoSerializer(source='detallepedido_set', many=True, read_only=True)
    class Meta:
        model = Pedido
        fields = ['id', 'sucursal', 'fecha', 'detalle']

class ContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacto
        fields = ['nombre', 'email', 'mensaje', 'fecha']
