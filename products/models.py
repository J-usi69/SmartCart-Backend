from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    has_discount = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)


    related_products = models.ManyToManyField('self', blank=True, symmetrical=False,
                                              related_name='recommended_for')

    @property
    def final_price(self):
        if self.has_discount and self.discount_percentage > 0:
            discount = (self.price * self.discount_percentage) / 100
            return round(self.price - discount, 2)
        return self.price

    def save(self, *args, **kwargs):
        if self.stock <= 0:
            self.is_available = False
        else:
            self.is_available = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
