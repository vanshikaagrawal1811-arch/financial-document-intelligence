"""
pdf_extractor.py
-----------------
Extracts raw text from PDF files using PyMuPDF (fitz).

This is the FIRST step in our pipeline. Most digitally-generated PDFs
(like salary slips created in Word/Excel and exported to PDF) already
contain a text layer, so we can pull the text directly without OCR.

If this returns very little/no text, the calling code (app.py) will
fall back to OCR (see ocr.py) because the PDF is probably a scanned
image with no text layer.
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes):
    """
    Extract text from a PDF file.

    Args:
        file_bytes: raw bytes of the uploaded PDF file

    Returns:
        A string containing all text found in the PDF.
        Returns "" (empty string) if extraction fails or no text found.
    """
    try:
        # Open the PDF directly from memory - no need to save to disk first
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        full_text = ""
        for page in doc:
            full_text += page.get_text()

        doc.close()
        return full_text.strip()

    except Exception as e:
        # Never crash the app - just report the problem to the console
        print(f"[pdf_extractor] Error reading PDF: {e}")
        return ""


def pdf_has_readable_text(text, min_characters=30):
    """
    Simple heuristic: if the extracted text is too short, the PDF is
    probably a scanned image and needs OCR instead of plain extraction.
    """
    return len(text.strip()) >= min_characters
