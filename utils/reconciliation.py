"""Month-aware salary-credit reconciliation for the loan verification workflow."""
import re
import calendar
from datetime import datetime
import pandas as pd

MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): i for i, name in enumerate(calendar.month_abbr) if name})


def salary_period(text, filename=""):
    """Infer a salary period from common text formats or a filename."""
    patterns = [
        r"(?:for the month of|salary month|pay period|month)\s*[:\-]?\s*([A-Za-z]+\s+\d{4})",
        r"(?:for the month of|salary month|pay period|month)\s*[:\-]?\s*(\d{1,2}[/-]\d{4})",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            for fmt in ("%B %Y", "%b %Y", "%m/%Y", "%m-%Y"):
                try:
                    return datetime.strptime(value.title(), fmt).strftime("%Y-%m")
                except ValueError:
                    pass
            try:
                month, year = value.replace("-", "/").split("/")
                return f"{int(year):04d}-{int(month):02d}"
            except (ValueError, TypeError):
                pass
    match = re.search(r"(20\d{2})[-_](0[1-9]|1[0-2])", filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None


def match_salary_credits(salary_docs, transactions):
    """Match each payslip to salary-like credits in the same month.

    salary_docs: list of {period, net_salary, filename, employee_name}
    transactions: DataFrame containing date, description, amount, type.
    """
    if transactions is None or transactions.empty:
        transactions = pd.DataFrame(columns=["date", "description", "amount", "type"])
    tx = transactions.copy()
    if not tx.empty:
        tx["parsed_date"] = pd.to_datetime(tx["date"], format="%d-%b-%Y", errors="coerce")
        tx["period"] = tx["parsed_date"].dt.strftime("%Y-%m")
        descriptions = tx["description"].fillna("").str.lower()
        tx["salary_like"] = (tx["type"].astype(str).str.upper().eq("CREDIT") & descriptions.str.contains(r"salary|payroll|wage", regex=True))
    rows = []
    for doc in salary_docs:
        period, declared = doc.get("period"), doc.get("net_salary")
        candidates = tx[(tx["period"] == period) & tx["salary_like"]] if period and not tx.empty else tx.iloc[0:0]
        observed = float(candidates["amount"].sum()) if not candidates.empty else None
        diff = round(observed - float(declared), 2) if observed is not None and declared is not None else None
        if not period:
            status, message = "period_unknown", "Could not identify the payslip month; check the document or filename."
        elif declared is None:
            status, message = "missing_salary", "Net salary could not be extracted from the payslip."
        elif observed is None:
            status, message = "no_credit", "No salary-like credit was found in the bank statement for this month."
        elif abs(diff) <= 1:
            status, message = "matched", "Payslip net salary matches the identified bank salary credit(s)."
        else:
            status, message = "mismatch", f"Salary difference of ₹{abs(diff):,.2f}; verify the discrepancy."
        rows.append({"Period": period or "Unknown", "Payslip file": doc.get("filename", ""), "Payslip net salary (₹)": declared,
                     "Bank salary credit(s) (₹)": observed, "Difference (bank - payslip) (₹)": diff,
                     "Status": status.replace("_", " ").title(), "Explanation": message})
    return pd.DataFrame(rows)
