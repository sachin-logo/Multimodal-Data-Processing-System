from PIL import Image
import pytesseract
import os

def extract_image_text(image_path):
    # Allow explicit tesseract path via env var
    tess_cmd = os.getenv('TESSERACT_CMD')
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text
