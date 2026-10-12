"""
classifier.py
-------------
Detects which of the 3 supported document types the extracted text
belongs to: salary_slip, bank_statement, or invoice.

APPROACH: simple, transparent keyword scoring.
This is deliberately NOT a trained ML classifier - it is easy to
explain to judges: "we count how many salary-related words appear
vs bank-related words vs invoice-related words, and pick the winner."
"""

# Keywords that strongly suggest each document type.
# We lowercase the input text before matching, so keep these lowercase.
KEYWORDS = {
    "salary_slip": [
        "salary slip", "payslip", "pay slip", "basic salary", "hra",
        "gross salary", "net salary", "employee id", "employee name",
        "deductions", "earnings", "ctc",
    ],
    "bank_statement": [
        "bank statement", "account statement", "account number",
        "ifsc", "opening balance", "closing balance", "withdrawal",
        "deposit", "transaction date", "debit", "credit", "balance",
    ],
    "invoice": [
        "invoice", "invoice number", "invoice no", "bill to", "gst",
        "subtotal", "sub total", "tax", "total amount", "seller",
        "buyer", "quantity", "unit price",
    ],
}


def classify_document(text):
    """
    Score the text against each document type's keyword list and
    return the type with the highest score.

    Args:
        text: extracted document text (string)

    Returns:
        tuple: (document_type, scores_dict)
        document_type is one of: "salary_slip", "bank_statement",
        "invoice", or "unknown" if no keywords matched at all.
    """
    if not text or not text.strip():
        return "unknown", {}

    text_lower = text.lower()

    scores = {}
    for doc_type, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[doc_type] = score

    best_type = max(scores, key=scores.get)

    # If nothing matched at all, we genuinely don't know what this is
    if scores[best_type] == 0:
        return "unknown", scores

    return best_type, scores
