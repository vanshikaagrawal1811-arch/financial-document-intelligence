"""Income verification prototype for salaried personal-loan applications."""
import streamlit as st
import pandas as pd

from utils.pdf_extractor import extract_text_from_pdf, pdf_has_readable_text
from utils.ocr import extract_text_from_image, extract_text_from_scanned_pdf
from utils.classifier import classify_document
from utils.extractor import extract_salary_slip, extract_bank_statement
from utils.validator import find_missing_fields, validate_salary_slip
from utils.anomaly_detector import detect_anomalies
from utils.reconciliation import salary_period, match_salary_credits

st.set_page_config(page_title="Income Verification | Retail Lending", page_icon="📑", layout="wide")
st.title("Personal Loan · Income Verification")
st.caption("Document intelligence prototype for a fictional Indian retail bank | Synthetic data recommended")
st.info("Purpose: help loan operations staff check income-document consistency. Flags are review signals, not proof of fraud or loan approval decisions.")

with st.sidebar:
    st.header("Case setup")
    case_id = st.text_input("Application reference", "LN-DEMO-1024")
    st.caption("Upload up to three months of salary slips and the corresponding bank statement PDF(s).")
    st.divider()
    st.markdown("**Expected documents**\n- Salary slips (ideally 3 months)\n- Bank statement(s) covering the same period")
    st.markdown("**Supported formats**\nPDF, PNG, JPG/JPEG")

uploads = st.file_uploader("Upload salary slips and bank statement(s)", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

def read_upload(file):
    content = file.getvalue()
    name = file.name.lower()
    if name.endswith(".pdf"):
        text = extract_text_from_pdf(content)
        if pdf_has_readable_text(text):
            return text, "PDF text extraction"
        return extract_text_from_scanned_pdf(content), "OCR (scanned PDF)"
    return extract_text_from_image(content), "OCR (image)"

if uploads:
    salary_docs, transaction_frames, document_rows, processing_errors = [], [], [], []
    with st.spinner("Extracting and checking uploaded documents..."):
        for file in uploads:
            try:
                text, method = read_upload(file)
                doc_type, _ = classify_document(text)
                row = {"File": file.name, "Detected type": doc_type.replace("_", " ").title(), "Extraction": method, "Result": "Processed" if text.strip() else "No text extracted"}
                document_rows.append(row)
                if doc_type == "salary_slip":
                    data = extract_salary_slip(text)
                    salary_docs.append({"period": salary_period(text, file.name), "net_salary": data.get("net_salary"),
                                        "filename": file.name, "employee_name": data.get("employee_name"), "data": data,
                                        "missing": find_missing_fields("salary_slip", data), "issues": validate_salary_slip(data)})
                elif doc_type == "bank_statement":
                    header, tx = extract_bank_statement(text)
                    if not tx.empty:
                        tx["source_file"] = file.name
                        transaction_frames.append(tx)
                elif doc_type == "unknown":
                    processing_errors.append(f"{file.name}: document type was not recognized.")
            except Exception as exc:
                processing_errors.append(f"{file.name}: {exc}")

    transactions = pd.concat(transaction_frames, ignore_index=True) if transaction_frames else pd.DataFrame()
    st.subheader("1 · Document intake")
    st.dataframe(pd.DataFrame(document_rows), use_container_width=True, hide_index=True)
    if processing_errors:
        for error in processing_errors:
            st.warning(error)

    st.subheader("2 · Extracted payslip summary")
    if salary_docs:
        salary_table = pd.DataFrame([{"Month": d["period"] or "Unknown", "File": d["filename"], "Employee": d["data"].get("employee_name"),
                                      "Employer": d["data"].get("company"), "Gross salary (₹)": d["data"].get("gross_salary"),
                                      "Deductions (₹)": d["data"].get("deductions"), "Net salary (₹)": d["net_salary"]} for d in salary_docs])
        st.dataframe(salary_table, use_container_width=True, hide_index=True)
        if len(salary_docs) < 3:
            st.warning(f"Only {len(salary_docs)} payslip(s) uploaded. Three months are recommended for a more useful consistency check.")
    else:
        st.warning("No salary slips were recognized. Check the file format and document text.")

    st.subheader("3 · Month-by-month salary reconciliation")
    if salary_docs and not transactions.empty:
        reconciliation = match_salary_credits(salary_docs, transactions)
        st.dataframe(reconciliation, use_container_width=True, hide_index=True)
        matched = int(reconciliation["Status"].eq("Matched").sum())
        mismatches = int(reconciliation["Status"].eq("Mismatch").sum())
        missing_credits = int(reconciliation["Status"].eq("No Credit").sum())
        a, b, c = st.columns(3)
        a.metric("Months matched", f"{matched}/{len(reconciliation)}")
        b.metric("Salary mismatches", mismatches)
        c.metric("Months without salary credit", missing_credits)
        st.caption("Salary-like credits are identified from transaction descriptions and month. Descriptions can be inconsistent; review the underlying transactions before drawing conclusions.")
    else:
        reconciliation = pd.DataFrame()
        st.info("Upload at least one recognized payslip and a bank statement containing parseable transactions to run reconciliation.")

    st.subheader("4 · Transaction anomaly review")
    if not transactions.empty:
        anomaly_input = transactions.drop(columns=["source_file"], errors="ignore")
        anomaly_result = detect_anomalies(anomaly_input)
        if len(anomaly_result) < 10:
            st.warning("Few transactions are available. Isolation Forest results on small samples can be unstable and should be treated as exploratory only.")
        total = len(anomaly_result)
        flagged = int(anomaly_result["is_anomaly"].sum())
        a, b = st.columns(2)
        a.metric("Transactions analyzed", total)
        b.metric("Potential outliers", flagged)
        if flagged:
            st.dataframe(anomaly_result.loc[anomaly_result["is_anomaly"], ["date", "description", "amount", "type", "balance", "anomaly_score"]], use_container_width=True, hide_index=True)
        else:
            st.success("No transactions were flagged by this model in the uploaded sample.")
        st.caption("Isolation Forest detects statistical outliers, not fraud. Results depend on the transactions supplied and are not a calibrated fraud probability.")
    else:
        anomaly_result = pd.DataFrame()
        st.info("No bank transactions were parsed from the uploaded statements.")

    st.subheader("5 · Verification outcome")
    reasons = []
    if not salary_docs:
        reasons.append("No recognized payslip")
    if salary_docs and len(salary_docs) < 3:
        reasons.append("Fewer than three payslip months provided")
    if not transactions.empty and not reconciliation.empty:
        if reconciliation["Status"].isin(["Mismatch", "No Credit", "Missing Salary", "Period Unknown"]).any():
            reasons.append("One or more salary reconciliation exceptions")
    elif salary_docs:
        reasons.append("Bank-statement reconciliation unavailable")
    if any(d["missing"] or d["issues"] for d in salary_docs):
        reasons.append("Missing or inconsistent payslip fields")
    if not transactions.empty and "is_anomaly" in anomaly_result and anomaly_result["is_anomaly"].any():
        reasons.append("Potential transaction outliers require review")

    if reasons:
        st.warning("**Recommended next step: manual review**\n\n" + "\n".join(f"- {reason}" for reason in dict.fromkeys(reasons)))
    else:
        st.success("No configured exceptions were detected. This means only that these checks passed; it is not loan approval or proof that documents are authentic.")

    report_parts = [f"Personal Loan Income Verification Report\nApplication reference: {case_id}\nGenerated by: Financial Document Intelligence prototype\n", "DOCUMENTS\n" + pd.DataFrame(document_rows).to_csv(index=False)]
    if salary_docs:
        report_parts.append("PAYSLIP SUMMARY\n" + salary_table.to_csv(index=False))
    if not reconciliation.empty:
        report_parts.append("SALARY RECONCILIATION\n" + reconciliation.to_csv(index=False))
    if not transactions.empty:
        report_parts.append("TRANSACTIONS\n" + transactions.to_csv(index=False))
    report_parts.append("\nImportant: this report provides preliminary verification signals only. It does not establish fraud, creditworthiness, or loan approval.")
    st.download_button("Download verification report (CSV bundle)", data="\n\n".join(report_parts), file_name=f"{case_id}_verification_report.txt", mime="text/plain")
else:
    st.markdown("### How it works")
    st.markdown("1. Upload payslips for up to three months and bank statement(s).\n2. Extract key fields and transaction rows.\n3. Match salary-like credits to the payslip month.\n4. Review mismatches and potential transaction outliers.\n5. Export a verification report for a human reviewer.")
    st.markdown("**Demo tip:** sample text documents and a PDF conversion script are included in `sample_documents/`.")

st.divider()
st.caption("Portfolio simulation for a fictional retail bank. Use synthetic or properly authorized data only.")
