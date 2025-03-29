import os
import pytest
from verification.services.classifier import guess_document_type
from verification.services.ner import extract_entities
from verification.services.ocr import extract_text_from_file


# ------------------------
# 🔍 Классификатор
# ------------------------
def test_classifier_identity():
    text = "Удостоверение личности Иванов Иван"
    assert guess_document_type(text) == "identity"


def test_classifier_income():
    text = "Справка о доходах сотрудника за 2023 год"
    assert guess_document_type(text) == "income"


def test_classifier_supporting():
    text = "Подтверждающий документ на лечение"
    assert guess_document_type(text) == "supporting"


# ------------------------
# 🔍 NER (Natasha)
# ------------------------
def test_ner_entity_extraction():
    text = "Иванов Иван родился в Алматы и работает в Kaspi"
    entities = extract_entities(text)
    types = [e['type'] for e in entities]

    assert 'PER' in types or 'LOC' in types or 'ORG' in types


# ------------------------
# 🔍 OCR (на примере встроенного изображения)
# ------------------------
def test_ocr_on_sample_image():
    sample_path = os.path.join(os.path.dirname(__file__), 'sample_id.jpg')

    if not os.path.exists(sample_path):
        pytest.skip("Sample image not found")

    text = extract_text_from_file(sample_path)
    assert len(text.strip()) > 30  # Должен вернуть осмысленный текст
