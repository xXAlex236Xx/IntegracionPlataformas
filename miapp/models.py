# miapp/models.py
from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True, primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Stock(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stock_registros')
    cantidad = models.IntegerField()

    class Meta:
        unique_together = ('producto', 'sucursal')
        verbose_name_plural = "Stock"

    def __str__(self):
        return f"{self.cantidad} de {self.producto.nombre} en {self.sucursal.nombre}"

class Pedido(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)

    def __str__(self):
        return f"Pedido {self.id} en {self.sucursal.nombre} ({'Completado' if self.completado else 'Pendiente'})"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    # TEMPORARY: Set null=True for migration, then remove after first migrate
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True) 

    def save(self, *args, **kwargs):
        if not self.precio_unitario and self.producto: # Ensure producto exists
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} para Pedido {self.pedido.id}"

class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    # Option 1: Make it nullable for existing rows, then add a default for new ones.
    # asunto = models.CharField(max_length=200, blank=True, null=True) 
    # Option 2: Provide a fixed default for existing rows, while keeping it non-nullable for new ones
    asunto = models.CharField(max_length=200, default='Consulta General') # Added default string
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje de {self.nombre} - {self.asunto}"