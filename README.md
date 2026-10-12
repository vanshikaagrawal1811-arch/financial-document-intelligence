# Financial Document Intelligence

An AI-assisted **personal-loan income verification** prototype for a fictional Indian retail bank. It helps a loan-operations analyst compare a salaried applicant's payslips with salary-like credits in their bank statement over multiple months, identify exceptions, and prepare a review report.

> This is a portfolio simulation, not a product deployed by a real bank. It does not approve/decline loans or establish fraud. Use synthetic or properly authorized documents only.

## Business problem

Loan operations teams may need to manually inspect multiple payslips and bank statement pages to confirm that declared monthly net salary is consistent with credits received. This prototype automates the initial extraction and comparison so reviewers can focus on exceptions.

## Core workflow

1. Upload up to three months (or more) of salary slips and bank statement PDFs/images.
2. Extract text with PyMuPDF; use Tesseract OCR as a fallback for scanned PDFs and images.
3. Classify documents and extract key salary fields and bank transaction rows.
4. Infer each payslip's month and match it to salary-like bank credits in that month.
5. Report matched months, differences, missing salary-like credits, and missing/invalid payslip fields.
6. Run an exploratory Isolation Forest over bank transactions to surface statistical outliers for manual review.
7. Export a verification report containing the extracted summary, reconciliation results, and transactions.

## What it checks

- Payslip month, employee/employer labels, gross salary, deductions and net salary (where present in document text).
- Salary-like credit matching by month using transaction descriptions containing terms such as `salary`, `payroll`, or `wage`.
- Difference between the payslip's net salary and identified salary-like credits for the same month.
- Potential transaction outliers, with the warning that an outlier is not evidence of fraud.

## Limitations

- Extraction is regex/template-based; documents with unfamiliar layouts may require parser updates or manual correction.
- Matching depends on transaction descriptions. Banks and employers may use different narrations, split salary credits, or pay salary near month-end. Inspect exceptions rather than treating them as conclusions.
- A month can only be reconciled if the payslip period and transaction dates are parsed correctly.
- Isolation Forest is unsupervised and exploratory. Its flags are not fraud probabilities and can be unstable on small samples.
- This prototype does not verify employer identity, document authenticity, credit bureau records, or loan eligibility. A human reviewer remains responsible for decisions.
- OCR fallback requires the Tesseract system executable in addition to the Python package.

## Tech stack

- Python, Streamlit
- PyMuPDF and pytesseract/Pillow for text extraction and OCR
- pandas and NumPy for tabular processing
- scikit-learn Isolation Forest for exploratory anomaly detection

## Run locally (Windows, macOS, Linux)

Python 3.10–3.12 recommended.

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:
```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. Upload files from `sample_documents/salary/` and `sample_documents/bank/`. The `.txt` files are for reference; convert them to PDFs using:

```bash
python sample_documents/convert_to_pdf.py
```

The script creates PDF versions beside each sample text file. The sample data is entirely fictional and intentionally includes a February salary mismatch and a one-time large credit to demonstrate review signals.

## Suggested GitHub repository description

`AI-assisted multi-month salary verification for personal-loan applications using PDF/OCR extraction, bank-credit reconciliation, and exploratory anomaly detection.`

## Responsible-use note

Do not upload real customer financial documents to a public repository or use real account data in screenshots. Keep credentials and private data out of Git. In production, add authentication, access controls, secure storage, retention/deletion policies, logging, and legal/compliance review before processing customer data.
