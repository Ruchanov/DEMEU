import re

CATEGORY_REQUIREMENTS = {
    'medicine': [
        'диагноз', 'счет', 'инвалидность', 'финансирование', 'история болезни'
    ],
    'education': [
        'аттестат', 'диплом', 'академические достижения', 'мотивационное письмо', 'рекомендательное письмо'
    ],
    'ecology': [
        'экологическая инициатива', 'разрешительные документы', 'оценка воздействия'
    ],
    'emergency': [
        'чрезвычайная ситуация', 'справка полиции', 'справка мчс', 'социальное обслуживание'
    ],
    'charity': [
        'уязвимая группа', 'семейное положение', 'план использования средств'
    ],
    'animals': [
        'ветеринарное заключение', 'приют', 'защита животных'
    ],
    'general': [
        'нуждающиеся', 'целевое использование', 'общественная инициатива'
    ],
    'sports': [
        'участник', 'соревнование', 'мероприятие', 'сертификат', 'диплом'
    ],
}


def validate_identity_document(text: str) -> bool:
    """
    Проверка удостоверения личности: наличие имени, даты рождения, ИИН
    """
    name_match = re.search(r'\b[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+\b', text)
    birth_match = re.search(r'(\d{2}[./-]\d{2}[./-]\d{4})|(\d{4}-\d{2}-\d{2})', text)
    iin_match = re.search(r'\b\d{12}\b', text)
    return all([name_match, birth_match, iin_match])


def validate_income_document(text: str) -> bool:
    """
    Проверка справки о доходах: наличие слова доход, зарплата, тенге и суммы
    """
    keywords = ['доход', 'зарплата', 'справка', 'тенге', '₸']
    has_keyword = any(k in text.lower() for k in keywords)
    amount_match = re.search(r'\b\d{4,}\b', text)
    return has_keyword and bool(amount_match)


def validate_supporting_document(text: str, category: str) -> dict:
    """
    Проверка документов по категории: ищем ключевые слова
    """
    required = CATEGORY_REQUIREMENTS.get(category, [])
    found = [k for k in required if k.lower() in text.lower()]
    return {
        'valid': bool(found),
        'found_keywords': found,
        'expected_keywords': required
    }

def guess_document_type(text: str) -> str:
    text = text.lower()

    if any(keyword in text for keyword in ['паспорт', 'удостоверение', 'фамилия', 'имя', 'иин']):
        return 'identity'
    elif any(keyword in text for keyword in ['справка о доходах', 'доход', 'зарплата', 'налоговая декларация']):
        return 'income'
    elif any(keyword in text for keyword in [
        'медицина', 'диагноз', 'обучение', 'экология', 'спорт', 'чрезвычайная',
        'приют', 'помощь', 'документ', 'финансирование', 'участие',
        'сертификат', 'мотивационное письмо', 'проект', 'пожар', 'болезнь']):
        return 'supporting'
    else:
        return 'supporting'  # По умолчанию
