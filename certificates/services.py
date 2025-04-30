from datetime import timedelta
from django.utils import timezone
from publications.models import Publication
from comments.models import Comment
from donations.models import Donation
from .models import UserCertificate, CertificateLevel
from .utils import generate_certificate_pdf

from django.core.mail import EmailMessage
from django.conf import settings

def determine_certificate_level(user):
    days_since_joined = (timezone.now().date() - user.date_joined.date()).days
    publications_count = Publication.objects.filter(author=user).count()
    comments_count = Comment.objects.filter(author=user).count()
    donations_count = Donation.objects.filter(publication__author=user).count()

    if days_since_joined >= 30 and publications_count >= 5 and donations_count >= 3:
        return CertificateLevel.GOLD
    elif publications_count >= 3 and comments_count >= 5:
        return CertificateLevel.SILVER
    elif days_since_joined >= 7 and publications_count >= 1:
        return CertificateLevel.BRONZE
    else:
        return None


def assign_certificate(user):
    level = determine_certificate_level(user)
    if not level:
        return None

    cert, _ = UserCertificate.objects.update_or_create(
        user=user,
        defaults={'level': level}
    )

    cert_file = generate_certificate_pdf(user, level)
    cert.pdf.save(cert_file.name, cert_file, save=True)

    return cert


def send_certificate_email(user, certificate):
    subject = f"🎉 You've received a {certificate.level.capitalize()} Certificate from DEMEU!"
    message = f"""
    <p>Dear {user.first_name},</p>

    <p>Congratulations! Based on your activity and contributions, you've been awarded a <strong>{certificate.level.capitalize()}</strong> certificate on the DEMEU platform.</p>

    <p>The certificate is attached to this email as a PDF file.</p>

    <p>Keep up the amazing work!</p>

    <p>Sincerely,<br>Team DEMEU</p>
    """

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = "html"

    if certificate.pdf:
        email.attach(certificate.pdf.name, certificate.pdf.read(), 'application/pdf')

    email.send(fail_silently=False)