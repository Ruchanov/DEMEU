from datetime import timedelta
from django.utils import timezone
from publications.models import Publication
from comments.models import Comment
from donations.models import Donation
from .models import UserCertificate, CertificateLevel
from .utils import generate_certificate_pdf

from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Sum

LEVEL_REQUIREMENTS = {
    "bronze": {
        "min_days": 7,
        "min_donations": 3,
    },
    "silver": {
        "min_days": 30,
        "min_comments": 3,
        "min_donations": 5,
        "min_total_amount": 30000,
    },
    "gold": {
        "min_days": 90,
        "min_comments": 10,
        "min_donations": 10,
        "min_total_amount": 50000,
    }
}

def determine_certificate_level(user):
    days_since_joined = (timezone.now().date() - user.date_joined.date()).days
    comments_count = Comment.objects.filter(author=user).count()
    donations_qs = Donation.objects.filter(donor=user)
    # donations_qs = Donation.objects.filter(publication__author=user)  # <- если нужно учитывать ПОЛУЧЕННЫЕ
    donations_count = donations_qs.count()
    total_donated = donations_qs.aggregate(total=Sum('amount'))['total'] or 0

    if (
        days_since_joined >= LEVEL_REQUIREMENTS["gold"]["min_days"]
        and comments_count >= LEVEL_REQUIREMENTS["gold"]["min_comments"]
        and donations_count >= LEVEL_REQUIREMENTS["gold"]["min_donations"]
        and total_donated >= LEVEL_REQUIREMENTS["gold"]["min_total_amount"]
    ):
        return CertificateLevel.GOLD

    elif (
        days_since_joined >= LEVEL_REQUIREMENTS["silver"]["min_days"]
        and comments_count >= LEVEL_REQUIREMENTS["silver"]["min_comments"]
        and donations_count >= LEVEL_REQUIREMENTS["silver"]["min_donations"]
        and total_donated >= LEVEL_REQUIREMENTS["silver"]["min_total_amount"]
    ):
        return CertificateLevel.SILVER

    elif (
        days_since_joined >= LEVEL_REQUIREMENTS["bronze"]["min_days"]
        and donations_count >= LEVEL_REQUIREMENTS["bronze"]["min_donations"]
    ):
        return CertificateLevel.BRONZE

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