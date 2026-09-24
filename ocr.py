import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_image(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    return gray.filter(ImageFilter.SHARPEN)

def extract_text(image: Image.Image) -> str:
    processed = preprocess_image(image)
    return pytesseract.image_to_string(processed)
