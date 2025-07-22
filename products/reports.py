from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from orders.models import Order, OrderItem
from datetime import datetime, timedelta
import os
import logging


logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import io
    from xhtml2pdf import pisa
    from django.template.loader import get_template
    from django.http import HttpResponse
    DEPENDENCIES_LOADED = True
except ImportError as e:
    logger.error(f"Error importando dependencias para reportes: {str(e)}")
    DEPENDENCIES_LOADED = False
    
    class MockPD:
        def DataFrame(self, *args, **kwargs): 
            logger.warning("Intento de usar pandas.DataFrame pero pandas no está instalado")
            return []
        def ExcelWriter(self, *args, **kwargs): 
            logger.warning("Intento de usar pandas.ExcelWriter pero pandas no está instalado")
            return type('obj', (object,), {'__enter__': lambda s: s, '__exit__': lambda s, *a, **k: None})
    pd = MockPD()
    io = type('io', (), {'BytesIO': type('BytesIO', (), {'seek': lambda s, *a: None, 'read': lambda s: b''})})
    pisa = type('pisa', (), {'CreatePDF': lambda *a, **k: type('PisaStatus', (), {'err': True})()})
    def get_template(template_src):
        logger.warning(f"Intento de cargar plantilla {template_src} pero django-xhtml2pdf no está instalado")
        return type('Template', (), {'render': lambda s, ctx: ''})
    HttpResponse = lambda *args, **kwargs: None


def generate_client_report(client_id, start_date=None, end_date=None):
    try:
        orders = Order.objects.filter(user_id=client_id)

        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:

            end_of_day = datetime.combine(end_date.date(), datetime.max.time())
            orders = orders.filter(created_at__lte=end_of_day)

        orders_data = []
        for order in orders:
            items = OrderItem.objects.filter(order=order)
            orders_data.append({
                'id': order.id,
                'date': order.created_at,
                'total': order.total,
                'status': order.status,
                'items': [
                    {
                        'product': item.product.name,
                        'price': item.price,
                        'quantity': item.quantity,
                        'subtotal': item.price * item.quantity
                    } for item in items
                ]
            })

        return {
            'client_id': client_id,
            'start_date': start_date,
            'end_date': end_date,
            'orders': orders_data,
            'total_spent': sum(order['total'] for order in orders_data) if orders_data else 0
        }
    except Exception as e:
        logger.exception(f"Error al generar reporte de cliente: {str(e)}")
        raise


def generate_top_products_report(start_date=None, end_date=None, limit=10):
    try:
        query = OrderItem.objects.values('product__id', 'product__name')

        if start_date:
            query = query.filter(order__created_at__gte=start_date)
        if end_date:

            end_of_day = datetime.combine(end_date.date(), datetime.max.time())
            query = query.filter(order__created_at__lte=end_of_day)

        top_products = query.annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('price')
        ).order_by('-total_sold')[:limit]

        return {
            'start_date': start_date,
            'end_date': end_date,
            'top_products': list(top_products)
        }
    except Exception as e:
        logger.exception(f"Error al generar reporte de productos más vendidos: {str(e)}")
        raise


def export_to_excel(data, report_type):
    if not DEPENDENCIES_LOADED:
        logger.error("No se pueden exportar datos a Excel: pandas no está instalado")
        raise ImportError("Pandas no está instalado. Instala pandas para exportar a Excel.")
    
    try:
        buffer = io.BytesIO()

        if report_type == 'client':

            if not data['orders']:
                orders_df = pd.DataFrame(columns=['Orden ID', 'Fecha', 'Total', 'Estado'])
                items_df = pd.DataFrame(columns=['Orden ID', 'Producto', 'Precio', 'Cantidad', 'Subtotal'])
            else:
                orders_df = pd.DataFrame([
                    {
                        'Orden ID': order['id'],
                        'Fecha': order['date'],
                        'Total': order['total'],
                        'Estado': order['status']
                    } for order in data['orders']
                ])

                items_data = []
                for order in data['orders']:
                    for item in order['items']:
                        items_data.append({
                            'Orden ID': order['id'],
                            'Producto': item['product'],
                            'Precio': item['price'],
                            'Cantidad': item['quantity'],
                            'Subtotal': item['subtotal']
                        })
                items_df = pd.DataFrame(items_data) if items_data else pd.DataFrame(columns=['Orden ID', 'Producto', 'Precio', 'Cantidad', 'Subtotal'])

            with pd.ExcelWriter(buffer) as writer:
                orders_df.to_excel(writer, sheet_name='Órdenes', index=False)
                items_df.to_excel(writer, sheet_name='Detalles', index=False)

        elif report_type == 'top_products':
            if not data['top_products']:
                df = pd.DataFrame(columns=['ID Producto', 'Nombre', 'Cantidad Vendida', 'Ingreso Total'])
            else:
                df = pd.DataFrame(data['top_products'])
                df.columns = ['ID Producto', 'Nombre', 'Cantidad Vendida', 'Ingreso Total']
            df.to_excel(buffer, index=False)

        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.exception(f"Error al exportar a Excel: {str(e)}")
        raise


def render_to_pdf(template_src, context_dict):
    if not DEPENDENCIES_LOADED:
        logger.error("No se puede generar PDF: xhtml2pdf no está instalado")
        raise ImportError("xhtml2pdf no está instalado. Instala xhtml2pdf para generar PDF.")
    
    try:
        template = get_template(template_src)
        html = template.render(context_dict)
        result = io.BytesIO()

        pisa_status = pisa.CreatePDF(html, dest=result)

        if pisa_status.err:
            logger.error(f"Error al generar PDF: {pisa_status.err}")
            return None

        result.seek(0)
        return result
    except Exception as e:
        logger.exception(f"Error al renderizar PDF: {str(e)}")
        return None
