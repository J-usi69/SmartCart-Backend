from decimal import Decimal

from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from .permissions import IsStaffOrSuperUser
from orders.models import Cart
from django.http import HttpResponse
from datetime import datetime
import logging
from .simple_reports import ClientReportGenerator, TopProductsReportGenerator

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.method not in ['GET'] and not request.user.is_staff:
            self.permission_denied(request)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Product.objects.all()

        return Product.objects.filter(is_available=True, stock__gt=0)

    @action(detail=True, methods=['post'])
    def apply_discount(self, request, pk=None):
        product = self.get_object()
        try:
            discount_str = str(request.data.get('discount_percentage', '0'))
            discount = float(discount_str)
            if discount < 0 or discount > 100:
                return Response(
                    {"error": "El descuento debe estar entre 0 y 100%"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product.discount_percentage = Decimal(discount_str)
            product.has_discount = discount > 0
            product.save()

            return Response({
                "message": f"Descuento del {discount}% aplicado correctamente",
                "product": ProductSerializer(product).data
            })
        except (ValueError, TypeError):
            return Response(
                {"error": "Valor de descuento inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def bulk_discount(self, request):
        product_ids = request.data.get('product_ids', [])

        if not product_ids:
            return Response(
                {"error": "Debe proporcionar al menos un ID de producto"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            discount_str = str(request.data.get('discount_percentage', '0'))
            discount = float(discount_str)
            if discount < 0 or discount > 100:
                return Response(
                    {"error": "El descuento debe estar entre 0 y 100%"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            products = Product.objects.filter(id__in=product_ids)
            decimal_discount = Decimal(discount_str)
            count = products.update(
                discount_percentage=decimal_discount,
                has_discount=discount > 0
            )
            return Response({
                "message": f"Descuento del {discount}% aplicado a {count} productos"
            })
        except (ValueError, TypeError):
            return Response(
                {"error": "Valor de descuento inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        user = request.user

        if not user.is_authenticated:
            return Response({"error": "Usuario no autenticado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            cart = Cart.objects.get(user=user)
            cart_products = [item.product for item in cart.items.all()]

            if not cart_products:
                recommendations = Product.objects.filter(
                    is_active=True,
                    is_available=True
                ).order_by('-id')[:5]
            else:
                recommendations = Product.objects.filter(
                    is_active=True,
                    is_available=True,
                    recommended_for__in=cart_products
                ).exclude(id__in=[p.id for p in cart_products]).distinct()[:5]

            return Response(ProductSerializer(recommendations, many=True).data)

        except Cart.DoesNotExist:
            recommendations = Product.objects.filter(
                is_active=True,
                is_available=True
            ).order_by('-id')[:5]
            return Response(ProductSerializer(recommendations, many=True).data)


@api_view(['GET'])
@permission_classes([IsStaffOrSuperUser])
def simple_client_report_view(request):

    try:
        client_id = request.GET.get('client_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        report_format = request.GET.get('format', 'pdf').lower()

        if not client_id:
            return HttpResponse("Error: Se requiere un ID de cliente", status=400)

        start_date = None
        end_date = None
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Error de formato de fecha: {str(e)}")
            return HttpResponse(f"Error: Formato de fecha inválido. Use YYYY-MM-DD. Detalle: {str(e)}", status=400)

        report_generator = ClientReportGenerator()

        if report_format == 'excel':
            return report_generator.generate_excel_report(client_id, start_date, end_date)
        else:  # Default is PDF
            return report_generator.generate_pdf_report(client_id, start_date, end_date)

    except Exception as e:
        logger.exception(f"Error inesperado en simple_client_report_view: {str(e)}")
        return HttpResponse(f"Error interno del servidor: {str(e)}", status=500)


@api_view(['GET'])
@permission_classes([IsStaffOrSuperUser])
def simple_top_products_report_view(request):

    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        limit = request.GET.get('limit', 10)
        report_format = request.GET.get('format', 'pdf').lower()

        start_date = None
        end_date = None
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            limit = int(limit)
        except ValueError as e:
            logger.error(f"Error de formato: {str(e)}")
            return HttpResponse(f"Error: Formato de fecha o límite inválido. Detalle: {str(e)}", status=400)

        report_generator = TopProductsReportGenerator()

        if report_format == 'excel':
            return report_generator.generate_excel_report(start_date, end_date, limit)
        else:  # Default is PDF
            return report_generator.generate_pdf_report(start_date, end_date, limit)

    except Exception as e:
        logger.exception(f"Error inesperado en simple_top_products_report_view: {str(e)}")
        return HttpResponse(f"Error interno del servidor: {str(e)}", status=500)
