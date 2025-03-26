from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import hashlib

from django.conf import settings
from .models import User
from .utils import generate_verification_token, send_email_dynamic
from django.core.mail import send_mail


@shared_task
def send_verification_email_task(user_id):
    try:
        user = User.objects.get(pk=user_id)

        token = generate_verification_token()
        user.set_verification_token(token)
        user.verification_token_expiry = timezone.now() + timedelta(hours=24)
        user.save()

        verification_url = f"{settings.SITE_URL}/accounts/verify-email/{token}/"
        subject = "Email Verification"
        html_message = f"""
            <html>
                <body>
                    <p>Thank you for registering on our site!</p>
                    <p>Please confirm your email by clicking the button below:</p>
                    <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; color: white; background-color: #007BFF; text-decoration: none; border-radius: 5px;">
                        Confirm Email
                    </a>
                </body>
            </html>
        """
        send_email_dynamic(subject, html_message, user.email)
    except User.DoesNotExist:
        # Можно логировать или просто игнорировать
        pass


@shared_task
def send_account_locked_email_task(email):
    subject = "Account Locked"
    message = "Your account has been locked due to too many failed login attempts."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        # Можно логировать ошибку, если нужно
        pass