DOCUMENT_REQUIREMENTS = {
    'identity': ['фамилия', 'имя', 'дата рождения', 'иин', 'удостоверение', 'паспорт'],
    'income': ['доход', 'зарплата', 'справка о доходах', 'налоговая декларация'],
    'supporting': ['медицинская справка', 'чек', 'фактура', 'письмо', 'подтверждение'],
}

CATEGORY_DOCUMENT_HINTS = {
    'medicine': [
        'диагноз', 'лечение', 'инвалидность', 'история болезни', 'счет на лечение',
        'госпиталь', 'медицинский центр', 'финансирование'
    ],
    'education': [
        'аттестат', 'диплом', 'счет учебного заведения', 'академические достижения',
        'мотивационное письмо', 'рекомендательное письмо', 'образование', 'университет'
    ],
    'ecology': [
        'экологический проект', 'оценка воздействия', 'разрешение', 'инициатива',
        'окружающая среда'
    ],
    'emergency': [
        'чрезвычайная ситуация', 'мчс', 'пожар', 'полиция', 'социальное обслуживание'
    ],
    'charity': [
        'социально уязвимая группа', 'семейное положение', 'план использования средств'
    ],
    'animals': [
        'приют', 'животные', 'ветеринар', 'защита животных', 'опека', 'питомец'
    ],
    'general': [
        'целевое использование', 'общественная инициатива', 'помощь', 'добровольцы'
    ],
    'sports': [
        'соревнование', 'спорт', 'участие', 'мероприятие', 'сертификат', 'достижение', 'спортсмены'
    ]
}


def validate_document_content(document_type, category, text):
    """
    Проверка текста OCR-документа на наличие обязательных слов по типу и категории
    """
    errors = []
    warnings = []
    matches = []

    text = text.lower()

    # Проверка по document_type
    type_keywords = DOCUMENT_REQUIREMENTS.get(document_type, [])
    type_found = [word for word in type_keywords if word in text]

    if not type_found:
        errors.append(f"Текст не соответствует ключевым словам для типа документа '{document_type}'")
    else:
        matches.extend(type_found)

    # Проверка по категории публикации
    category_keywords = CATEGORY_DOCUMENT_HINTS.get(category, [])
    category_found = [word for word in category_keywords if word in text]

    if not category_found:
        warnings.append(f"Нет подтверждения, что документ относится к категории '{category}'")
    else:
        matches.extend(category_found)

    result = {
        "matches": matches,
        "type_keywords_matched": type_found,
        "category_keywords_matched": category_found,
        "errors": errors,
        "warnings": warnings
    }

    return result
