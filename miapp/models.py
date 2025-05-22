# miapp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings # Import settings to get AUTH_USER_MODEL

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

# --- NEW MODELS FOR SHOPPING CART ---

class Cart(models.Model):
    # Links to the User model configured in settings.AUTH_USER_MODEL
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    # For anonymous users, we can store a session key to persist the cart
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Carrito de {self.user.username}"
        elif self.session_key:
            return f"Carrito (sesión: {self.session_key[:5]}...)" # Show first 5 chars of session key
        return "Carrito Anónimo"

    def get_total_price(self):
        """Calculates the total price of all items in the cart."""
        # Sums the total price of each CartItem
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        """Calculates the total number of individual items (sum of quantities) in the cart."""
        # Sums the quantity of each CartItem
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1) # Quantity must be positive
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures that a specific product can only appear once in a given cart
        unique_together = ('cart', 'producto') 

    def __str__(self):
        return f"{self.quantity} x {self.producto.nombre} en carrito de {self.cart}"

    def get_total_price(self):
        """Calculates the total price for this specific cart item."""
        return self.quantity * self.producto.precio