import os
from PIL import Image
from pdf2image import convert_from_path
import cv2
import numpy as np
import pytesseract


def extract_text_from_file(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        pages = convert_from_path(file_path, dpi=300)
        image = pages[0]
    else:
        image = Image.open(file_path)

    # Preprocessing
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 10)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(thresh, -1, kernel)

    temp_path = file_path + "_processed.png"
    cv2.imwrite(temp_path, sharpened)

    text = pytesseract.image_to_string(Image.open(temp_path), lang='kaz+rus+eng')

    os.remove(temp_path)
    return text.strip()
