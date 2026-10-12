"""
extractor.py
------------
Pulls structured fields out of raw document text using regular
expressions (regex). This is deliberately rule-based and deterministic
- no ML, no LLM required - so every extracted number can be traced
back to an exact pattern you can show to hackathon judges.

Each function below matches ONE document type and returns a plain
Python dict of the fields described in the project spec.

If a field can't be found, its value is set to None so that
validator.py can later report it as "missing".
"""

import re
import pandas as pd


# ---------------------------------------------------------------------
# Small shared helper
# ---------------------------------------------------------------------

def _parse_amount(raw_value):
    """
    Convert a matched amount string like "1,20,000" or "₹ 5000" or
    "5000.50" into a float. Returns None if it can't be parsed.
    """
    if raw_value is None:
        return None
    cleaned = raw_value.replace(",", "").replace("₹", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _search_amount(pattern, text):
    """Run a regex search and return the first group as a parsed amount."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return _parse_amount(match.group(1))
    return None


def _search_text(pattern, text):
    """Run a regex search and return the first group as a stripped string."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


# ---------------------------------------------------------------------
# SALARY SLIP
# ---------------------------------------------------------------------

def extract_salary_slip(text):
    """
    Extract fields from a salary slip's text.

    Expected fields (see project spec):
        employee_name, employee_id, company, basic_salary, hra,
        bonus, gross_salary, deductions, net_salary
    """
    data = {
        "document_type": "salary_slip",
        "employee_name": _search_text(r"Employee Name[:\s]+([A-Za-z .]+)", text),
        "employee_id": _search_text(r"Employee ID[:\s]+([A-Za-z0-9\-]+)", text),
        "company": _search_text(r"(?:Company(?: Name)?|COMPANY)[:\s]+([A-Za-z0-9 .&]+)", text),
        "basic_salary": _search_amount(r"Basic Salary[:\s]*₹?\s*([\d,]+)", text),
        "hra": _search_amount(r"\bHRA[:\s]*₹?\s*([\d,]+)", text),
        "bonus": _search_amount(r"Bonus(?:/Allowance)?[:\s]*₹?\s*([\d,]+)", text),
        "gross_salary": _search_amount(r"Gross Salary[:\s]*₹?\s*([\d,]+)", text),
        "deductions": _search_amount(r"Deductions[:\s]*₹?\s*([\d,]+)", text),
        "net_salary": _search_amount(r"Net Salary[:\s]*₹?\s*([\d,]+)", text),
    }
    return data


# ---------------------------------------------------------------------
# BANK STATEMENT
# ---------------------------------------------------------------------

def extract_bank_statement(text):
    """
    Extract header fields + a transaction table from bank statement text.

    Expects transaction lines in this pipe-separated format (matching
    our sample documents):
        01-Jan-2026 | Salary Credit - ABC Technologies | 48000 | CREDIT | 68000
        <date> | <description> | <amount> | <CREDIT/DEBIT> | <balance>

    Returns:
        tuple: (header_data_dict, transactions_dataframe)
    """
    header = {
        "document_type": "bank_statement",
        "account_holder": _search_text(r"Account Holder[:\s]+([A-Za-z .]+)", text),
        "opening_balance": _search_amount(r"Opening Balance[:\s]*₹?\s*([\d,]+)", text),
    }

    # Transaction line pattern: date | description | amount | type | balance
    # Balance can be negative (an overdrawn account), so we allow an
    # optional leading "-" on that final number.
    transaction_pattern = re.compile(
        r"(\d{1,2}-[A-Za-z]{3}-\d{4})\s*\|\s*(.+?)\s*\|\s*([\d,]+)\s*\|\s*"
        r"(CREDIT|DEBIT)\s*\|\s*(-?[\d,]+)",
        re.IGNORECASE,
    )

    rows = []
    for match in transaction_pattern.finditer(text):
        date_str, description, amount_str, txn_type, balance_str = match.groups()
        rows.append({
            "date": date_str,
            "description": description.strip(),
            "amount": _parse_amount(amount_str),
            "type": txn_type.upper(),
            "balance": _parse_amount(balance_str),
        })

    transactions_df = pd.DataFrame(rows)
    return header, transactions_df


# ---------------------------------------------------------------------
# INVOICE
# ---------------------------------------------------------------------

def extract_invoice(text):
    """
    Extract fields from invoice text, including a list of line items.

    Expects item lines in this pipe-separated format (matching our
    sample documents):
        Laptop Stand | 2 | 1500 | 3000
        <item name> | <quantity> | <unit price> | <line amount>
    """
    data = {
        "document_type": "invoice",
        "invoice_number": _search_text(r"Invoice Number[:\s]+([A-Za-z0-9\-]+)", text),
        "seller": _search_text(r"Seller[:\s]+([A-Za-z0-9 .&]+)", text),
        "buyer": _search_text(r"Buyer[:\s]+([A-Za-z0-9 .&]+)", text),
        "subtotal": None,
        "tax": None,
        "total": None,
        "items": [],
    }

    # Line items: "Name | qty | unit_price | amount"
    item_pattern = re.compile(
        r"^(?!Subtotal|Total|GST|Tax)([A-Za-z0-9 .]+?)\s*\|\s*(\d+)\s*\|\s*"
        r"([\d,]+)\s*\|\s*([\d,]+)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    for match in item_pattern.finditer(text):
        name, qty, unit_price, amount = match.groups()
        data["items"].append({
            "name": name.strip(),
            "quantity": int(qty),
            "unit_price": _parse_amount(unit_price),
            "amount": _parse_amount(amount),
        })

    # Go line-by-line for subtotal / tax / total to avoid "Total" also
    # matching inside "Subtotal"
    for line in text.splitlines():
        line_lower = line.lower()
        if "subtotal" in line_lower or "sub total" in line_lower:
            data["subtotal"] = _search_amount(r"([\d,]+)\s*$", line)
        elif "gst" in line_lower or "tax" in line_lower:
            data["tax"] = _search_amount(r"([\d,]+)\s*$", line)
        elif line_lower.strip().startswith("total"):
            data["total"] = _search_amount(r"([\d,]+)\s*$", line)

    return data
