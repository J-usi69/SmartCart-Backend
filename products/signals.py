from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from pyexpat.errors import messages

from users.models import Usuario
from .models import Product

@receiver(post_save, sender=Product)
def notify_low_stock(sender,instance, **kwargs):
    if instance.stock < 5:
        admins = Usuario.objects.filter(rol=1,is_active=True)
        recipient_list=[admin.correo for admin in admins if admin.correo]

        if recipient_list:
            subject = f"Stock bajo para el producto: {instance.name}"
            message = (
                f"Estimado Administrador,\n\n"
                f"El producto '{instance.name}' tiene un stock bajo de {instance.stock} unidades.\n"
                f"Por favor, considere reabastecerlo lo antes posible.\n\n"
                f"SmartCart System"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )
