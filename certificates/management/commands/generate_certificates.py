from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from certificates.services import assign_certificate

User = get_user_model()

class Command(BaseCommand):
    help = 'Reassign and regenerate PDF for users with certificate level'

    def handle(self, *args, **kwargs):
        users = User.objects.filter(certificate__isnull=False)
        for user in users:
            cert = assign_certificate(user)
            if cert and cert.pdf:
                self.stdout.write(self.style.SUCCESS(f"{user.email}: PDF regenerated."))
            else:
                self.stdout.write(self.style.WARNING(f"{user.email}: No certificate assigned or PDF failed."))
