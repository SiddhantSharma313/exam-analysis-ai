import logging
import tempfile
from pathlib import Path

from pdf2image import convert_from_bytes
from pytesseract import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_from_pdf(pdf_bytes: bytes, dpi: int = 300) -> str:
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    text_parts: list[str] = []
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        text_parts.append(text)
    return "\n".join(text_parts).strip()
