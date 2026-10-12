# Financial Document Intelligence

An AI-assisted **personal-loan income verification prototype** for a fictional Indian retail bank. The application helps a loan-operations analyst compare a salaried applicant's payslips with salary-like credits in bank statements across multiple months, identify exceptions, and generate a verification report.

> **Portfolio project:** This is a demonstration prototype, not a product deployed by a real bank. It does not approve or reject loans and cannot establish fraud. Use synthetic or properly authorized documents only.

## Business problem

Loan-operations teams may need to inspect multiple payslips and bank-statement pages to assess whether declared monthly net salary is consistent with credits received. Manual checks can be time-consuming and inconsistencies may be overlooked. This project automates the initial extraction and comparison so a reviewer can focus on exceptions.

## Workflow

1. Upload payslips and a bank statement covering multiple months.
2. Extract document text using PyMuPDF; use Tesseract OCR as a fallback for scanned PDFs and images.
3. Classify documents and extract relevant salary fields and bank-transaction rows.
4. Infer the payslip month and match it to salary-like bank credits for that month.
5. Compare net salary with identified credits and flag differences, missing credits, or missing/invalid payslip fields.
6. Apply an exploratory Isolation Forest model to surface statistically unusual transactions for manual review.
7. Review the results in the Streamlit interface and export a verification report.

## Key features

- **Document extraction:** Reads text-based PDFs and supports OCR fallback for scanned documents and images.
- **Payslip field extraction:** Looks for employee/employer labels, salary period, gross salary, deductions, and net salary when present in the document text.
- **Multi-month reconciliation:** Compares payslip net salary with salary-like credits in the corresponding month.
- **Exception reporting:** Highlights mismatches, missing salary-like credits, and incomplete or invalid payslip fields.
- **Transaction anomaly detection:** Uses Isolation Forest to surface potential outliers for manual review.
- **Report export:** Exports extracted summaries, reconciliation results, and transaction-level review signals.
- **Synthetic sample documents:** Includes example payslips and bank statements for demonstrating the workflow without exposing real customer data.

## Example use case

The sample dataset includes three monthly payslips and a bank statement covering the same period. It intentionally includes a February salary discrepancy and a large one-time credit to demonstrate how the system can surface items for review.

The system reports the difference and supporting details; it does **not** conclude that a discrepancy is fraud. A reviewer must investigate exceptions before making any decision.

## Technology stack

- **Language:** Python
- **Interface:** Streamlit
- **PDF extraction:** PyMuPDF
- **OCR:** pytesseract and Pillow, with the Tesseract system executable required for OCR fallback
- **Data processing:** pandas and NumPy
- **Anomaly detection:** scikit-learn Isolation Forest

## Run locally

Python 3.10–3.12 is recommended.

### 1. Clone the repository

```bash
git clone https://github.com/vanshikaagrawal1811-arch/financial-document-intelligence.git
cd financial-document-intelligence
```

### 2. Create and activate a virtual environment

**Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the application

```bash
streamlit run app.py
```

Open the local URL printed in the terminal by Streamlit.

## Sample documents

Sample documents are located in `sample_documents/`, with payslips in `sample_documents/salary/` and bank statements in `sample_documents/bank/`. Upload the PDF samples through the application. The accompanying `.txt` files are readable references; to regenerate PDFs from the text samples, run:

```bash
python sample_documents/convert_to_pdf.py
```

The sample data is fictional and includes deliberate exceptions for demonstration purposes.

## Limitations

- Extraction is regex/template-based; unfamiliar document layouts may require parser updates or manual correction.
- Isolation Forest is unsupervised and exploratory. Its flags are not fraud probabilities and may be unstable on small datasets.
- OCR fallback requires the Tesseract system executable in addition to the Python package.
- Human review is required before acting on any discrepancy or anomaly.

