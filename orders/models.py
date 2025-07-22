from django.db import models
from users.models import Usuario
from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('preparandola', 'Preparandola'),
        ('en camino', 'En camino'),
        ('entregada', 'Entregada'),
        ('cancelada', 'Cancelada'),
    )

    client = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='orders')
    delivery_user = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='deliveries')

    products = models.ManyToManyField(Product, through='OrderItem')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.client.correo}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    previous_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.id} - {self.previous_status} ➔ {self.new_status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order {self.order.id})"


class Cart(models.Model):
    user = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.user.correo}"

    @property
    def total_price(self):
        return sum(item.product.final_price * item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} en carrito de {self.cart.user.correo}"