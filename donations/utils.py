import os
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from .models import Donation
from donations.signals import (
    check_publication_funding,
    notify_goal_reached,
    notify_half_goal_reached,
    notify_new_donation
)
from donations.tasks import send_donation_email_task
from .receipt import generate_donation_receipt

def handle_donation_created(donation):
    """
    Выполняет все необходимые действия после создания пожертвования.
    Используется как в обычной форме, так и при Stripe-платежах.
    """
    check_publication_funding(type(donation), donation, created=True)
    notify_half_goal_reached(type(donation), donation, created=True)
    notify_goal_reached(type(donation), donation, created=True)
    notify_new_donation(type(donation), donation, created=True)
    send_donation_email_task.delay(donation.id)


def send_donation_email(donor, donation):
    subject = "Спасибо за ваше пожертвование!"
    message = f"""
    Уважаемый {donor.first_name if donor else "Анонимный донор"},

    Спасибо за ваше пожертвование на публикацию '{donation.publication.title}'.
    В приложении вы найдете чек о вашем пожертвовании.

    С уважением,
    Команда Demeu
    """

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [donor.email])

    # Генерируем PDF-чек и прикрепляем к письму
    pdf_buffer = generate_donation_receipt(donation)
    email.attach(f"donation_receipt_{donation.id}.pdf", pdf_buffer.getvalue(), "application/pdf")

    email.send()
