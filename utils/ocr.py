"""
ocr.py
------
Fallback text extraction using Tesseract OCR.

Used when:
  - The uploaded file is an image (PNG/JPG/JPEG), OR
  - The uploaded PDF has no extractable text layer (i.e. it is a
    scanned document, not a digitally generated one)

Requires the Tesseract OCR *engine* to be installed on the operating
system (this is separate from the "pytesseract" Python package, which
is just a wrapper around it). See README.md for install instructions.
"""

import io
from PIL import Image
import pytesseract
import fitz  # used to convert PDF pages into images before OCR


def extract_text_from_image(file_bytes):
    """
    Run OCR on an image file (PNG/JPG/JPEG).

    Args:
        file_bytes: raw bytes of the uploaded image

    Returns:
        Extracted text as a string ("" if OCR fails)
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"[ocr] Error reading image: {e}")
        return ""


def extract_text_from_scanned_pdf(file_bytes):
    """
    Run OCR on a PDF that has no text layer, by rendering each page
    as an image first, then running OCR on that image.

    Args:
        file_bytes: raw bytes of the uploaded PDF

    Returns:
        Combined OCR text from all pages ("" if it fails)
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = ""

        for page in doc:
            # Render the page to an image at a reasonable resolution
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            full_text += pytesseract.image_to_string(image) + "\n"

        doc.close()
        return full_text.strip()

    except Exception as e:
        print(f"[ocr] Error running OCR on PDF: {e}")
        return ""
