from PIL import Image
import pytesseract

# Укажи путь до tesseract.exe, если он не добавлен в PATH
# У тебя он находится по этому пути:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Путь к изображению
# image_path = "django.png"  # замени на путь к своему изображению

#Полный путь к изображению
image_path = r"C:\Users\admin\Downloads\techorda.jpg"

# Распознавание текста (поддержка русского и английского)
text = pytesseract.image_to_string(Image.open(image_path), lang="kaz+rus+eng")

print("Распознанный текст:")
print(text)