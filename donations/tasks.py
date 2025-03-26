from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Donation
from .utils import generate_donation_receipt


@shared_task
def send_donation_email_task(donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)
        donor = donation.donor

        if donor and donor.email:
            subject = "Спасибо за ваше пожертвование!"
            message = f"""
            Уважаемый {donor.first_name if donor else "Анонимный донор"},

            Спасибо за ваше пожертвование на публикацию '{donation.publication.title}'.
            В приложении вы найдете чек о вашем пожертвовании.

            С уважением,
            Команда Demeu
            """

            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [donor.email])

            # Генерация PDF-чека
            pdf_buffer = generate_donation_receipt(donation)
            email.attach(f"donation_receipt_{donation.id}.pdf", pdf_buffer.getvalue(), "application/pdf")

            email.send()

    except Donation.DoesNotExist:
        # Можно логировать ошибку или игнорировать
        pass
