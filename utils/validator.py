"""
validator.py
------------
Three jobs:
  1. Check for MISSING required fields in extracted document data.
  2. Check financial CALCULATIONS are internally consistent
     (e.g. Basic + HRA + Bonus should equal Gross Salary).
  3. CROSS-DOCUMENT verification - compare a salary slip's declared
     income against what actually shows up as a credit in a bank
     statement.

All checks here are plain, deterministic Python - no ML, no LLM.
This is intentional: financial arithmetic should be checked with
exact rules, not statistical guesses.
"""

# Fields required for each document type (used for missing-field checks)
REQUIRED_FIELDS = {
    "salary_slip": [
        "employee_name", "employee_id", "company",
        "basic_salary", "hra", "bonus",
        "gross_salary", "deductions", "net_salary",
    ],
    "bank_statement": [
        "account_holder", "opening_balance",
    ],
    "invoice": [
        "invoice_number", "seller", "buyer",
        "subtotal", "tax", "total",
    ],
}

# Small tolerance for rounding differences (₹1 wiggle room)
TOLERANCE = 1.0


def find_missing_fields(document_type, data):
    """
    Return a list of required field names that are missing (None or
    empty) in the extracted data dict.
    """
    required = REQUIRED_FIELDS.get(document_type, [])
    missing = []
    for field in required:
        value = data.get(field)
        if value is None or value == "":
            missing.append(field)
    return missing


def validate_salary_slip(data):
    """
    Check:
      Basic Salary + HRA + Bonus = Gross Salary
      Gross Salary - Deductions = Net Salary

    Returns a list of human-readable issue strings (empty = all good).
    """
    issues = []

    basic = data.get("basic_salary")
    hra = data.get("hra")
    bonus = data.get("bonus")
    gross = data.get("gross_salary")
    deductions = data.get("deductions")
    net = data.get("net_salary")

    # Only run a check if every number involved is actually present
    if None not in (basic, hra, bonus, gross):
        expected_gross = basic + hra + bonus
        if abs(expected_gross - gross) > TOLERANCE:
            issues.append(
                f"Gross Salary Inconsistency: expected ₹{expected_gross:,.0f}, "
                f"found ₹{gross:,.0f}"
            )

    if None not in (gross, deductions, net):
        expected_net = gross - deductions
        if abs(expected_net - net) > TOLERANCE:
            issues.append(
                f"Net Salary Inconsistency: expected ₹{expected_net:,.0f}, "
                f"found ₹{net:,.0f}"
            )

    return issues


def validate_invoice(data):
    """
    Check:
      Sum of item amounts ≈ Subtotal
      Subtotal + Tax ≈ Total

    Returns a list of human-readable issue strings.
    """
    issues = []

    items = data.get("items", [])
    subtotal = data.get("subtotal")
    tax = data.get("tax")
    total = data.get("total")

    if items and subtotal is not None:
        items_sum = sum(item.get("amount", 0) or 0 for item in items)
        if abs(items_sum - subtotal) > TOLERANCE:
            issues.append(
                f"Item Total Inconsistency: items sum to ₹{items_sum:,.0f}, "
                f"subtotal says ₹{subtotal:,.0f}"
            )

    if None not in (subtotal, tax, total):
        expected_total = subtotal + tax
        if abs(expected_total - total) > TOLERANCE:
            issues.append(
                f"Invoice Total Inconsistency: expected ₹{expected_total:,.0f}, "
                f"found ₹{total:,.0f}"
            )

    return issues


def cross_verify_salary(salary_data, bank_transactions_df, mismatch_threshold=0.15):
    """
    Compare declared salary (from the salary slip's Net Salary) against
    the salary credit actually observed in the bank statement.

    We look for a bank transaction whose description mentions "salary"
    and treat its amount as the "observed" salary credit.

    Args:
        salary_data: extracted salary slip dict
        bank_transactions_df: DataFrame of bank transactions
        mismatch_threshold: fractional difference allowed before we
            flag a mismatch (0.15 = 15%)

    Returns:
        dict with keys: declared, observed, status, message
        Returns None if there isn't enough information to compare.
    """
    declared = salary_data.get("net_salary")
    if declared is None or bank_transactions_df is None or bank_transactions_df.empty:
        return None

    if "description" not in bank_transactions_df.columns:
        return None

    salary_rows = bank_transactions_df[
        bank_transactions_df["description"].str.contains("salary", case=False, na=False)
        & (bank_transactions_df["type"].str.upper() == "CREDIT")
    ]

    if salary_rows.empty:
        return None

    observed = salary_rows["amount"].iloc[0]
    diff_ratio = abs(declared - observed) / declared if declared else 0

    if diff_ratio > mismatch_threshold:
        status = "mismatch"
        message = (
            f"⚠ Declared salary (₹{declared:,.0f}) does not match "
            f"observed salary credit (₹{observed:,.0f})."
        )
    else:
        status = "match"
        message = "✓ Declared salary matches observed bank credit."

    return {
        "declared": declared,
        "observed": observed,
        "status": status,
        "message": message,
    }
