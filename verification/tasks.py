from celery import shared_task
import os
import hashlib
import cv2
import numpy as np
from django.conf import settings
from PIL import Image
from pdf2image import convert_from_path
from publications.models import PublicationDocument
from verification.services.ocr import extract_text_from_file
from verification.services.ner import extract_entities
from verification.services.classifier import guess_document_type
from verification.services.validation import validate_document_content
from publications.utils import send_email_dynamic
from notifications.utils import notify_user

def preprocess_image(file_path):
    if file_path.lower().endswith('.pdf'):
        pages = convert_from_path(
            file_path, dpi=300,
            poppler_path=r'C:\Program Files\poppler-24.08.0\Library\bin'
        )
        image = pages[0]
    else:
        image = Image.open(file_path)

    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(thresh, -1, kernel)

    temp_path = file_path + '_processed.png'
    cv2.imwrite(temp_path, sharpened)
    return temp_path


@shared_task
def process_document_verification(document_id):
    try:
        document = PublicationDocument.objects.get(id=document_id)
    except PublicationDocument.DoesNotExist:
        return  # Документ уже удалён — задача безопасно завершена

    file_path = os.path.join(settings.MEDIA_ROOT, document.file.name)

    try:
        processed_path = preprocess_image(file_path)
        text = extract_text_from_file(processed_path)
        os.remove(processed_path)
        if not text.strip():
            document.verified = False
            document.verification_status = 'rejected'
            document.verification_details = {'error': 'Не удалось распознать текст документа.'}
            document.save()
            return

        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        document.text_hash = text_hash
        if PublicationDocument.objects.filter(text_hash=text_hash).exclude(id=document.id).exists():
            document.verified = False
            document.verification_status = 'rejected'
            document.verification_details = {'error': 'Документ уже был загружен ранее.'}
            document.save()
            return

        predicted_type = guess_document_type(text)
        entities = extract_entities(text)
        publication_category = document.publication.category

        validation_result = validate_document_content(
            document_type=document.document_type,
            category=publication_category,
            text=text
        )

        document.extracted_data = {
            "ocr_text": text,
            "predicted_type": predicted_type,
            "extracted_entities": entities,
            "validation": validation_result
        }

        if predicted_type != document.document_type or validation_result["errors"]:
            document.verified = False
            document.verification_status = 'rejected'
            document.verification_details = {
                "message": "Документ не соответствует требованиям.",
                "predicted_type": predicted_type,
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"]
            }

            subject = f'❌ Документ "{document.get_document_type_display()}" отклонён'
            message = f"""
                <p>Ваш документ "<strong>{document.get_document_type_display()}</strong>" был отклонён.</p>
                <p><strong>Причина:</strong> Документ не соответствует требованиям.</p>
                <p><strong>AI-определение типа:</strong> {predicted_type}</p>
                <p><strong>Ошибки:</strong> {', '.join(validation_result["errors"])}</p>
            """
        else:
            document.verified = True
            document.verification_status = 'approved'
            document.verification_details = {
                "message": "Документ успешно подтверждён",
                "predicted_type": predicted_type,
                "matches": validation_result["matches"]
            }

            subject = f'✅ Документ "{document.get_document_type_display()}" подтверждён'
            message = f"""
                <p>Ваш документ "<strong>{document.get_document_type_display()}</strong>" успешно подтверждён.</p>
                <p><strong>AI-определение типа:</strong> {predicted_type}</p>
                <p><strong>Найдено ключевых совпадений:</strong> {', '.join(validation_result["matches"])}</p>
            """

        document.save()


        publication = document.publication
        documents = publication.documents.all()

        if any(doc.verification_status == 'rejected' for doc in documents):
            publication.verification_status = 'rejected'
            publication.status = 'pending'
        elif all(doc.verification_status == 'approved' for doc in documents):
            publication.verification_status = 'approved'
            publication.status = 'active'
        else:
            publication.verification_status = 'pending'
            publication.status = 'pending'

        publication.save()

        # Отправка уведомления пользователю
        if publication.verification_status == 'approved':
            notify_user(
                user=publication.author,
                verb="✅ Ваша публикация была одобрена",
                target=f"Публикация: {publication.title}",
                url=f"http://localhost:8000/publications/{publication.id}/"
            )
        elif publication.verification_status == 'rejected':
            notify_user(
                user=publication.author,
                verb="❌ Ваша публикация была отклонена",
                target=f"Публикация: {publication.title}",
                url=f"http://localhost:8000/publications/{publication.id}/"
            )

    except Exception as e:
        document.verified = False
        document.verification_status = 'rejected'
        document.verification_details = {'error': str(e)}
        document.save()


@shared_task
def check_publication_status():
    from publications.models import Publication
    from django.utils import timezone
    now = timezone.now()

    publications = Publication.objects.filter(status='active')
    for pub in publications:
        donated = pub.total_donated()
        if donated >= pub.amount:
            pub.status = 'successful'
            pub.is_archived = True
            pub.save()
        elif pub.expires_at and pub.expires_at <= now:
            pub.status = 'expired'
            pub.is_archived = True
            pub.save()
