from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem
from .models import OrderStatusHistory


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id','previous_status','new_status','changed_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity')

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_name', 'quantity')

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, required=False)

    class Meta:
        model = Cart
        fields = ('id', 'user', 'items','total_price')
        read_only_fields = ('user',)

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        user = request.user if request else None

        cart = Cart.objects.create(user=user)

        for item_data in items_data:
            CartItem.objects.create(cart=cart, **item_data)

        return cart

class OrderSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.correo', read_only=True)
    items = OrderItemSerializer(many=True, required=False)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True, source="orderstatushistory_set")

    class Meta:
        model = Order
        fields = ['id', 'client', 'client_email', 'status', 'status_history', 'total_price', 'created_at', 'items']
        read_only_fields = ['client', 'created_at']
        extra_kwargs = {
            'client': {'read_only': True},
            'total_price': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        user = request.user if request else None

        validated_data.pop('client', None)

        order = Order.objects.create(client=user, **validated_data)

        total_price = 0
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']


            OrderItem.objects.create(order=order, product=product, quantity=quantity)


            total_price += product.final_price * quantity


            product.stock -= quantity
            if product.stock <= 0:
                product.is_active = False
            product.save()

        order.total_price = total_price
        order.save()

        return order

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        if 'status' in validated_data:
            new_status = validated_data['status']

            if hasattr(user, 'rol') and user.rol.nombre.lower() == 'delivery':
                if new_status != 'entregada':
                    raise serializers.ValidationError("El repartidor solo puede marcar como 'entregada'.")

            if instance.status != new_status:
                from .models import OrderStatusHistory
                OrderStatusHistory.objects.create(
                    order=instance,
                    previous_status=instance.status,
                    new_status=new_status
                )

            instance.status = new_status

        instance.save()
        return instance