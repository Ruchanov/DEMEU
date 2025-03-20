import os
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from .models import Donation

def generate_donation_receipt(donation):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Styles
    pdf.setFillColor(colors.red)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(100, 750, "Demeu - Donation Successful")

    # Green Confirmation Bar
    pdf.setFillColor(colors.green)
    pdf.rect(100, 720, 400, 25, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(180, 728, "Donation Successfully Completed")

    # Donation Details
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(100, 690, f"Amount: {donation.donor_amount} KZT")
    pdf.drawString(300, 690, f"Fee: {donation.support_amount} KZT")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 670, f"Donation ID: {donation.id}")
    pdf.drawString(100, 650, f"Date: {donation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    donor_name = f"{donation.donor.first_name} {donation.donor.last_name}" if donation.donor else "Anonymous"
    pdf.drawString(100, 630, f"Donor Name: {donor_name}")

    # Payment Method (Masked)
    pdf.drawString(100, 610, "From: Kaspi Gold *XXXX")

    # Recipient (Publication Title)
    pdf.drawString(100, 590, f"To: {donation.publication.title}")

    # Footer
    pdf.setStrokeColor(colors.gray)
    pdf.line(100, 570, 400, 570)
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(100, 550, "Thank you for your support!")
    pdf.drawString(100, 535, "This receipt is automatically generated.")

    pdf.save()
    buffer.seek(0)
    return buffer

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
