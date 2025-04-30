import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.mail import EmailMessage

def generate_certificate_pdf(user, level):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    # Цветовая схема
    if level == 'gold':
        color = (212/255, 175/255, 55/255)  # золотой
    elif level == 'silver':
        color = (192/255, 192/255, 192/255)  # серебряный
    else:
        color = (205/255, 127/255, 50/255)  # бронзовый

    p.setFillColorRGB(*color)
    p.setFont("Helvetica-Bold", 30)
    p.drawCentredString(width / 2, height - 100, f"{level.capitalize()} Certificate")

    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 160, f"Awarded to: {user.first_name} {user.last_name}")
    p.drawCentredString(width / 2, height - 190, f"For contribution to DEMEU platform")
    p.drawCentredString(width / 2, height - 240, f"Email: {user.email}")
    p.drawCentredString(width / 2, height - 290, "DEMEU Team")

    p.save()

    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"{user.id}_{level}_certificate.pdf")


def send_certificate_email(user, certificate):
    if not certificate.pdf:
        return {"success": False, "message": "PDF not found."}

    subject = f"🎉 Ваш сертификат DEMEU ({certificate.level.upper()})"
    body = f"""
    <p>Здравствуйте, {user.first_name}!</p>
    <p>Поздравляем вас с получением {certificate.level.upper()} сертификата за вашу активность на платформе DEMEU.</p>
    <p>Вы можете скачать его по ссылке ниже или найти его в своём профиле:</p>
    <p><a href="{settings.SITE_URL}{certificate.pdf.url}">Скачать сертификат</a></p>
    <p>Спасибо, что помогаете другим 💙</p>
    """

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.content_subtype = "html"

    email.send(fail_silently=False)
    return {"success": True}
