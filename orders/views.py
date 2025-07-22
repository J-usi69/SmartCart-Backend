from decimal import Decimal
import stripe
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from SmartCartBackend import settings
from .permissions import IsOwnerOrAdminOrAssignedDelivery, IsCartOwner
from .models import Order, OrderItem, OrderStatusHistory, Cart, CartItem
from .serializers import OrderSerializer, OrderItemSerializer, CartSerializer, CartItemSerializer
from stripe.error import StripeError
from django.core.mail import EmailMessage
from .utils import generate_invoice_pdf
from .speech_processing import detectar_productos_en_texto
from products.models import Product

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrAdminOrAssignedDelivery]
    filter_backends = [filters.SearchFilter]
    search_fields = ['status', 'client__correo', 'delivery_user__correo']

    def get_queryset(self):
        user = self.request.user

        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()

        if user.is_staff or user.is_superuser:
            return Order.objects.all()
        elif hasattr(user, 'rol') and user.rol.nombre.lower() == 'delivery':
            return Order.objects.filter(delivery_user=user)
        else:
            return Order.objects.filter(client=user)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_status = old_instance.status

        instance = serializer.save()

        if old_status != instance.status:
            OrderStatusHistory.objects.create(
                order=instance,
                previous_status=old_status,
                new_status=instance.status,
            )

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsOwnerOrAdminOrAssignedDelivery]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return OrderItem.objects.all()
        elif hasattr(user, 'rol') and user.rol.nombre.lower() == 'delivery':
            return OrderItem.objects.filter(order__delivery_user=user)
        else:
            return OrderItem.objects.filter(order__client=user)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsCartOwner]
    filter_backends = [filters.SearchFilter]
    search_fields = ['client__correo']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Cart.objects.all()

        queryset = Cart.objects.filter(user=user)
        if not queryset.exists():
            return Cart.objects.none()

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            cart = get_object_or_404(Cart, user=request.user)
            line_items = []

            for item in cart.items.all():
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.product.name,
                        },
                        'unit_amount': int(item.product.price * 100),
                    },
                    'quantity': item.quantity,
                })

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='https://pos-frontend-production-fd0d.up.railway.app/Sucess',
                cancel_url='https://backenddjango-production-c48c.up.railway.app/payment-cancel',
                metadata={"user_id": request.user.id}
            )
            return Response({'checkout_url': session.url})

        except StripeError as e:
            return Response({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({'error': 'Invalid payload or signature'}, status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session.get('metadata', {}).get('user_id')

            if not user_id:
                return Response({'error': 'No user_id in metadata'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                cart = Cart.objects.get(user_id=user_id)

                if not cart.items.exists():
                    return Response({'error': 'Carrito vacío.'}, status=status.HTTP_400_BAD_REQUEST)

                order = Order.objects.create(
                    client=cart.user,
                    status='paid'
                )
                total_price = Decimal('0')
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity
                    )

                    product = item.product
                    product.stock -= item.quantity
                    product.save()

                    price = item.product.final_price
                    subtotal = price * item.quantity
                    total_price += subtotal

                order.total_price = total_price
                order.save()

                cart.delete()

                pdf_buffer = generate_invoice_pdf(order)

                email = EmailMessage(
                    subject=f"Tu recibo de compra - Orden #{order.id}",
                    body="Gracias por tu compra. Adjunto encontrarás tu recibo en PDF.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[order.client.correo],
                ) #aqui la cague, quite el {order.id}
                email.attach(f"recibo_orden_{order.id}.pdf", pdf_buffer.read(), "application/pdf")
                email.send()

                print(f"Pago exitoso para usuario {user_id}, orden {order.id} creada y carrito eliminado.")

            except Cart.DoesNotExist:
                return Response({'error': 'Carrito no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)


class VoiceCartProcessingView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        texto = request.data.get('texto')

        if not texto:
            return Response(
                {"error": "El texto de voz es obligatorio"},
                status=status.HTTP_400_BAD_REQUEST
            )


        productos = Product.objects.filter(is_active=True, is_available=True)
        productos_formateados = [
            {"id": p.id, "name": p.name.lower()} for p in productos
        ]

        #
        items_detectados = detectar_productos_en_texto(texto, productos_formateados)

        if not items_detectados:
            return Response(
                {"message": "No se detectaron productos en el texto"},
                status=status.HTTP_404_NOT_FOUND
            )


        cart, created = Cart.objects.get_or_create(user=request.user)


        added_items = []
        for item in items_detectados:
            product = Product.objects.get(id=item['product'])
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': item['quantity']}
            )


            if not created:
                cart_item.quantity += item['quantity']
                cart_item.save()

            added_items.append({
                'product': product.name,
                'quantity': item['quantity']
            })

        return Response({
            "message": "Productos agregados al carrito exitosamente",
            "added_items": added_items,
            "cart_total": cart.total_price
        }, status=status.HTTP_200_OK)