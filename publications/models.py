import os
import uuid
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from phonenumber_field.modelfields import PhoneNumberField
from datetime import timedelta


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


VERIFICATION_STATUS_CHOICES = [
    ('pending', 'Ожидает проверки'),
    ('approved', 'Подтверждена'),
    ('rejected', 'Отклонена'),
]

STATUS_CHOICES = [
    ('active', 'Активна'),
    ('successful', 'Успешно завершена'),
    ('pending', 'Ожидает проверки'),
    ('expired', 'Истёк срок'),
]

DURATION_CHOICES = [
    (7, "7 дней"),
    (14, "2 недели"),
    (30, "1 месяц"),
]

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active') #екущий статус публикации
    is_archived = models.BooleanField(default=False) #для фильтрации в архиве
    duration_days = models.IntegerField(choices=DURATION_CHOICES, default=30) #длительность публикации (7, 14, 30 дней)
    expires_at = models.DateTimeField(blank=True, null=True) #дата окончания
    verification_status = models.CharField(max_length=20,choices=VERIFICATION_STATUS_CHOICES,default='pending',
        help_text="Статус проверки всех загруженных документов")

    def total_donated(self):
        return self.donations.aggregate(total=Sum('donor_amount'))['total'] or 0

    def total_views(self):
        return self.views.count()

    def total_comments(self):
        return self.comments.count() if hasattr(self, 'comments') else 0

    def donation_percentage(self):
        total = self.total_donated()
        return (total / self.amount) * 100 if self.amount else 0

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.duration_days)
        super().save(*args, **kwargs)

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
    publication = models.ForeignKey('Publication', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to=publication_document_path,
        validators=[validate_document_format, validate_file_size]  # <-- здесь исправили
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    text_hash = models.CharField(max_length=64, unique=False, null=True, blank=True)
    # Поля проверки ИИ
    verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Ожидание проверки'),
            ('approved', 'Подтверждён'),
            ('rejected', 'Отклонён')
        ],
        default='pending'
    )
    verification_details = models.JSONField(null=True, blank=True)
    extracted_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.publication.title} - {self.get_document_type_display()}"

# class Donation(models.Model):
#     publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='donations')
#     donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
#                               related_name="donations")
#     donor_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(default=timezone.now)
#
#     def __str__(self):
#         donor_name = "Anonymous"
#         if self.donor:
#             donor_name = f"{self.donor.first_name} {self.donor.last_name}".strip()
#         return f"{donor_name} donated {self.donor_amount}"


class View(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.viewer} viewed publication {self.publication.title}"