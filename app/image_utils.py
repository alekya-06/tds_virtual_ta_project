import pytesseract
from PIL import Image
import io
import base64

def extract_text_from_image(image_base64: str) -> str:
    """Extracts text from base64 encoded image with error handling"""
    try:
        img = Image.open(io.BytesIO(base64.b64decode(image_base64)))
        return pytesseract.image_to_string(img)
    except Exception as e:
        raise ValueError(f"Image processing failed: {str(e)}")