from celery import shared_task
import pytesseract
from PIL import Image
from django.conf import settings
import os
from pdf2image import convert_from_path
from .models import PublicationDocument
import cv2
import numpy as np
import hashlib
from .utils import send_email_dynamic
from django.utils import timezone
# Natasha imports
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsNERTagger,
    Doc
)

# Natasha NER initialization
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)

@shared_task
def validate_document_ocr(document_id):
    document = PublicationDocument.objects.get(id=document_id)
    file_path = os.path.join(settings.MEDIA_ROOT, document.file.name)
    user_email = document.publication.author.email
    document_name = document.get_document_type_display()

    try:
        if file_path.lower().endswith('.pdf'):
            pages = convert_from_path(
                file_path, dpi=300,
                poppler_path=r'C:\Program Files\poppler-24.08.0\Library\bin'
            )
            image = pages[0]
        else:
            image = Image.open(file_path)

        # Предобработка изображения
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

        temp_image_path = file_path + "_processed.png"
        cv2.imwrite(temp_image_path, sharpened)

        # Извлечение текста OCR
        text = pytesseract.image_to_string(Image.open(temp_image_path),lang='kaz+rus+eng')
        print(f"Extracted Text: {text}")

        os.remove(temp_image_path)

        # Проверка дубликатов
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        document.text_hash = text_hash

        if PublicationDocument.objects.filter(text_hash=text_hash).exclude(id=document.id).exists():
            document.verified = False
            document.verification_status = 'rejected'
            document.verification_details = {'error': 'Документ уже был загружен ранее.'}
            document.save()

            subject = f'❌ Документ "{document_name}" отклонён'
            message = f"""
                <p>Ваш документ "<strong>{document_name}</strong>" был отклонён.</p>
                <p><strong>Причина:</strong> Документ уже был загружен ранее.</p>
            """
            send_email_dynamic(subject, message, user_email)
            return

        # Natasha NER-анализ
        doc = Doc(text)
        doc.segment(segmenter)
        doc.tag_ner(ner_tagger)

        # Извлечение и нормализация сущностей
        extracted_entities = []
        for span in doc.spans:
            span.normalize(morph_vocab)
            extracted_entities.append({
                'text': span.text,
                'type': span.type,
                'normal': span.normal
            })

        # Проверка ключевых слов по типам документов
        keywords_map = {
            'identity': ['удостоверение', 'паспорт', 'фамилия', 'имя'],
            'income': ['справка', 'доход', 'зарплата', 'заработок'],
            'supporting': ['документ', 'справка', 'подтверждение']
        }

        keywords = keywords_map.get(document.document_type, [])
        found_keywords = [word for word in keywords if word.lower() in text.lower()]

        if found_keywords:
            document.verified = True
            document.verification_status = 'approved'
            details = {
                'found_keywords': found_keywords,
                'extracted_entities': extracted_entities
            }

            subject = f'✅ Документ "{document_name}" успешно подтверждён'
            message = f"""
                <p>Ваш документ "<strong>{document_name}</strong>" успешно подтверждён.</p>
                <p><strong>Найденные ключевые слова:</strong> {', '.join(found_keywords)}</p>
                <p><strong>Извлечённые данные (NER):</strong> {', '.join([e['normal'] for e in extracted_entities])}</p>
            """
        else:
            document.verified = False
            document.verification_status = 'rejected'
            details = {
                'error': 'Ключевые слова не найдены.',
                'extracted_entities': extracted_entities
            }

            subject = f'❌ Документ "{document_name}" отклонён'
            message = f"""
                <p>Ваш документ "<strong>{document_name}</strong>" был отклонён.</p>
                <p><strong>Причина:</strong> Ключевые слова не найдены.</p>
                <p><strong>Извлечённые данные (NER):</strong> {', '.join([e['normal'] for e in extracted_entities])}</p>
            """

        document.verification_details = details
        document.extracted_data = details  # сохраняем извлеченные данные отдельно
        document.save()

        # Отправка email-уведомления
        send_email_dynamic(subject, message, user_email)

    except Exception as e:
        document.verified = False
        document.verification_status = 'rejected'
        document.verification_details = {'error': str(e)}
        document.save()

        subject = f'⚠️ Ошибка при проверке документа "{document_name}"'
        message = f"""
            <p>При проверке вашего документа "<strong>{document_name}</strong>" произошла ошибка:</p>
            <pre>{str(e)}</pre>
            <p>Пожалуйста, попробуйте загрузить документ снова.</p>
        """
        send_email_dynamic(subject, message, user_email)


@shared_task
def check_publication_status():
    print("🕒 Циклическая задача запущена: проверка публикаций")

    from .models import Publication
    from django.utils import timezone
    now = timezone.now()

    publications = Publication.objects.filter(status='active')
    for pub in publications:
        donated = pub.total_donated()
        if donated >= pub.amount:
            pub.status = 'successful'
            pub.is_archived = True
            pub.save()
            print(f"[✓] {pub.title} marked as successful.")
        elif pub.expires_at and pub.expires_at <= now:
            pub.status = 'expired'
            pub.is_archived = True
            pub.save()
            print(f"[⌛] {pub.title} expired and archived.")

