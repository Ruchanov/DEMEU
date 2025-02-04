from django.core.mail import send_mail
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from .models import Feedback
from .serializers import FeedbackSerializer

class FeedbackCreateView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        user = self.request.user
        feedback = serializer.save(
            user=user,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email
        )

        self.send_admin_notification(feedback)

    def send_admin_notification(self, feedback):
        subject = "New feedback on the website"
        message = f"""
        New feedback from {feedback.first_name} {feedback.last_name} ({feedback.email}):

        {feedback.text}

        Contact phone number: {feedback.phone_number}

        Images: {len(feedback.images.all())} uploaded
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
