from django.core.mail import send_mail
from django.conf import settings

def send_gmail_email(to_email, subject, html_content):
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        html_message=html_content,
    )