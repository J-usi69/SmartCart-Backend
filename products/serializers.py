from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    related_products_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_related_products_info(self, obj):

        return [
            {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'final_price': product.final_price
            } for product in obj.related_products.filter(
                is_active=True, is_available=True
            )[:3]
        ]
