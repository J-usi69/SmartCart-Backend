from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from users.views import RolViewSet, UsuarioViewSet, CustomPasswordResetView, LogoutView, PasswordResetConfirmView, \
    RegisterClienteView, RegisterDeliveryView, UserProfileView
from products.views import ProductViewSet
from orders.views import OrderViewSet, OrderItemViewSet, CartViewSet, CartItemViewSet, CheckoutView, StripeWebhookView, \
    VoiceCartProcessingView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

router = routers.DefaultRouter()
router.register(r'roles', RolViewSet)
router.register(r'users', UsuarioViewSet)
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'cart', CartViewSet, basename="cart")
router.register(r'cart-items', CartItemViewSet, basename="cart-items")

schema_view = get_schema_view(
    openapi.Info(
        title="SmartCart API",
        default_version='v1',
        description="Documentación de los endpoints del proyecto SmartCart",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="oerlinker@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/register-cliente/', RegisterClienteView.as_view(), name='register_cliente'),
    path('api/register-delivery/', RegisterDeliveryView.as_view(), name='register_delivery'),
    path('api/password-reset/', CustomPasswordResetView.as_view(), name='custom_password_reset'),
    path('api/reset-password-confirm/<uid>/<token>/', PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('api/checkout/', CheckoutView.as_view(), name='checkout'),
    path('api/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/products/', include('products.urls')),
    path('api/me/', UserProfileView.as_view(), name='user_profile'),
    path('api/voice-to-cart/', VoiceCartProcessingView.as_view(), name='voice-to-cart'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path('.well-known/assetlinks.json',
         serve,
         {'document_root': os.path.join(settings.BASE_DIR, '.well-known'),
          'path': 'assetlinks.json'}),
]
