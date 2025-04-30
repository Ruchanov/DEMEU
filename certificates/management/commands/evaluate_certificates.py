from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from certificates.services import assign_certificate

User = get_user_model()

class Command(BaseCommand):
    help = "Evaluate and assign user certificates"

    def handle(self, *args, **kwargs):
        users = User.objects.filter(is_active=True)
        for user in users:
            cert = assign_certificate(user)
            if cert:
                self.stdout.write(self.style.SUCCESS(f"✅ {user.email} assigned: {cert.level}"))
            else:
                self.stdout.write(f"— {user.email}: not eligible.")
