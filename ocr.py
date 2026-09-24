import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def preprocess_image(image: Image.Image) -> Image.Image:
    """Prepare an image for general OCR."""
    gray = image.convert("L")
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = gray.filter(ImageFilter.SHARPEN)

    # Upscale to help OCR recognize small or decorative text
    width, height = gray.size
    gray = gray.resize((width * 2, height * 2))

    return gray


def extract_text(image: Image.Image) -> str:
    """
    Run multiple OCR passes because alcohol labels may contain
    decorative headings, mixed font sizes, and dense warning text.
    """
    processed = preprocess_image(image)

    # Pass 1: Treat the label as a block of text
    standard_text = pytesseract.image_to_string(
        processed,
        config="--psm 6"
    )

    # Pass 2: Look for text distributed across the image
    sparse_text = pytesseract.image_to_string(
        processed,
        config="--psm 11"
    )

    # Pass 3: Give extra attention to the upper portion,
    # where brand names commonly appear
    width, height = processed.size
    upper_section = processed.crop((0, 0, width, int(height * 0.40)))

    brand_text = pytesseract.image_to_string(
        upper_section,
        config="--psm 6"
    )

    combined_text = "\n".join([
        standard_text,
        sparse_text,
        brand_text
    ])

    return combined_text
