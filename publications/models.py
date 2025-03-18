import os
import uuid
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from phonenumber_field.modelfields import PhoneNumberField


def validate_file_size(file):
    max_size = 50 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(f"Размер файла не может превышать {max_size / (1024 * 1024)} MB.")


def validate_video_format(file):
    valid_formats = ['mp4']
    if not file.name.split('.')[-1].lower() in valid_formats:
        raise ValidationError("Только видео в формате MP4 разрешены.")


def validate_image_format(file):
    valid_formats = ['jpg', 'jpeg', 'png']
    if not file.name.split('.')[-1].lower() in valid_formats:
        raise ValidationError("Только изображения в форматах JPG, JPEG, PNG разрешены.")


def validate_bank_details(value):
    if len(value) < 8 or len(value) > 30:
        raise ValidationError("Введите корректный номер карты.")

# Функция для хранения документов в каталоге MEDIA_ROOT/documents/publication_<id>/
def publication_document_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"publication_{instance.publication.id}_{instance.document_type}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("documents", f"publication_{instance.publication.id}", instance.document_type, filename)

# Валидация форматов файлов
def validate_document_format(file):
    valid_formats = ['jpg', 'jpeg', 'png', 'pdf']
    if not file.name.split('.')[-1].lower() in valid_formats:
        raise ValidationError("Разрешены только файлы форматов JPG, JPEG, PNG, PDF.")


def limit_publication_documents(instance):
    if instance.publication.documents.count() >= 5:
        raise ValidationError("Нельзя загружать более 5 документов на одну публикацию.")



# Models
class Publication(models.Model):
    CATEGORY_CHOICES = [
        ('medicine', 'Медицина'),
        ('emergency', 'Неотложная помощь'),
        ('charity', 'Благотворительность'),
        ('education', 'Образование'),
        ('animals', 'Животные'),
        ('ecology', 'Экология'),
        ('sports', 'Спорт'),
        ('general', 'Общий сбор средств'),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='publications'
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(max_length=3000)
    bank_details = models.CharField(max_length=30, validators=[validate_bank_details])
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                 help_text="Сумма, которую необходимо собрать.")
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = PhoneNumberField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_donated(self):
        return self.donations.aggregate(total=Sum('donor_amount'))['total'] or 0

    def total_views(self):
        return self.views.count()

    def total_comments(self):
        return self.comments.count()

    def donation_percentage(self):
        total = self.total_donated()
        return (total / self.amount) * 100 if self.amount else 0

    def __str__(self):
        return self.title


class PublicationImage(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='publications/images/', validators=[validate_file_size, validate_image_format])


class PublicationVideo(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='publications/videos/', validators=[validate_file_size, validate_video_format])


# Типы документов
DOCUMENT_TYPES = [
    ('identity', 'Удостоверение личности'),
    ('income', 'Справка о доходах'),
    ('supporting', 'Подтверждающие документы'),
]


# Модель документа
class PublicationDocument(models.Model):
    publication = models.ForeignKey(
        'Publication', on_delete=models.CASCADE, related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to=publication_document_path,
        validators=[validate_document_format, validate_file_size]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.publication.title} - {self.get_document_type_display()}"

class Donation(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    donor_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.donor_name} donated {self.donor_amount}"


class View(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.viewer} viewed publication {self.publication.title}"