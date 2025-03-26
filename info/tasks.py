from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from .models import Feedback


@shared_task
def send_admin_notification_task(feedback_id):
    try:
        feedback = Feedback.objects.get(id=feedback_id)
    except Feedback.DoesNotExist:
        return  # Можно залогировать ошибку, если нужно

    subject = "New Feedback Submission"
    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    admin_url = f"{site_url}{reverse('admin:info_feedback_change', args=[feedback.pk])}"
    message_text = feedback.text.replace("\n", "<br>")

    image_links = "".join(
        f'<li><a href="{site_url}{img.image.url}" target="_blank">{img.image.name}</a></li>'
        for img in feedback.images.all()
    ) or "<li>No images uploaded</li>"

    message_html = f"""
    <html>
    <body>
        <h2 style="color: #0078be;">New Feedback Received</h2>
        <p><strong>From:</strong> {feedback.first_name} {feedback.last_name} (<a href="mailto:{feedback.email}">{feedback.email}</a>)</p>
        <p><strong>Phone:</strong> {feedback.phone_number}</p>
        <p><strong>Theme:</strong> {feedback.theme}</p>
        <p><strong>Message:</strong></p>
        <blockquote style="border-left: 3px solid #0078be; padding-left: 10px; font-style: italic;">
            {message_text}
        </blockquote>
        <h3>Attachments</h3>
        <ul>{image_links}</ul>
        <p><a href="{admin_url}" style="display: inline-block; background-color: #0078be; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">View in Admin Panel</a></p>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body="New feedback received. Open in a web browser to view details.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.DEFAULT_FROM_EMAIL]
    )
    email.attach_alternative(message_html, "text/html")
    email.send()
