from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def generate_invoice_pdf(order):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica", 16)
    p.drawString(100, height - 50, f"Recibo de venta - Orden #{order.id}")
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Cliente: {order.client.nombre} {order.client.apellido}")
    p.drawString(100, height - 100, f"Correo: {order.client.correo}")
    p.drawString(100, height - 120, f"Fecha: {order.created_at.strftime('%d/%m/%Y')}")

    y = height - 160
    total = 0
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Productos Comprados:")
    p.setFont("Helvetica", 12)

    for item in order.items.all():
        y -= 20
        p.drawString(120, y, f"- {item.product.name} (x{item.quantity}) : ${item.product.price * item.quantity}")
        total += item.product.price * item.quantity

    y -= 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y, f"Total pagado: ${total}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
