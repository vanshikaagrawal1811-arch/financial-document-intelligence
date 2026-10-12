"""
convert_to_pdf.py
------------------
Converts all the sample .txt documents in this folder into simple
PDFs, so you can actually upload them into the Streamlit app and test
the full pipeline (PDF text extraction -> classification -> ...).

Uses PyMuPDF (fitz), which is already a project dependency - no extra
install needed.

Run from the project root:
    python sample_documents/convert_to_pdf.py

This will create a matching .pdf next to every .txt file found in
salary/, bank/, and invoices/.
"""

import os
import fitz  # PyMuPDF

FOLDERS = ["salary", "bank"]


def text_file_to_pdf(txt_path, pdf_path):
    """Create a simple one-page-per-chunk PDF containing the given text."""
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc = fitz.open()  # new empty PDF
    page = doc.new_page()

    # Simple text box starting near the top-left of the page
    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")

    doc.save(pdf_path)
    doc.close()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    converted = 0

    for folder in FOLDERS:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                txt_path = os.path.join(folder_path, filename)
                pdf_path = os.path.join(folder_path, filename.replace(".txt", ".pdf"))
                text_file_to_pdf(txt_path, pdf_path)
                print(f"Created: {pdf_path}")
                converted += 1

    print(f"\nDone. Converted {converted} file(s) to PDF.")


if __name__ == "__main__":
    main()
