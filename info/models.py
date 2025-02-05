import os
import re
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

def validate_phone_number(value):
    if not re.match(r'^\+\d{10,15}$', value):
        raise ValidationError("The phone number must start with '+' and contain between 10 and 15 digits.")

def validate_file_size(file):
    max_size = 10 * 1024 * 1024  # 10 MB
    if file.size > max_size:
        raise ValidationError(f"Размер файла не может превышать {max_size / (1024 * 1024)} MB.")

def validate_image_format(file):
    valid_formats = ['jpg', 'jpeg', 'png']
    if not file.name.split('.')[-1].lower() in valid_formats:
        raise ValidationError("Только изображения в форматах JPG, JPEG, PNG разрешены.")

def feedback_photo_upload_path(instance, filename):
    return os.path.join('feedback_photos', f'user_{instance.feedback.user.id}', filename)


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    theme = models.CharField(max_length=255)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=12, validators=[validate_phone_number])
    email = models.EmailField()
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback from {self.first_name} {self.last_name} ({self.email})"

class FeedbackImage(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=feedback_photo_upload_path, validators=[validate_file_size, validate_image_format])
