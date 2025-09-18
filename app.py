# app.py (Final Version with Whitespace Trimming)

import streamlit as st
import pandas as pd
import tempfile
import os
import logging
import re

from extractor.pdf_reader import read_pdf
from extractor.ocr import ocr_pdf
from extractor.llm_client import extract_summary_data
from extractor.parser import process_transactions
from extractor.excel_writer import create_final_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- MODIFIED FUNCTION ---
def find_matching_transaction_file(pdf_filename: str, transaction_files: list):
    """
    Finds the specific "INVOICE DETAILS" transaction file that corresponds
    to a given PDF filename, ignoring leading/trailing whitespace.
    """
    # Trim whitespace from the PDF filename just in case
    clean_pdf_filename = pdf_filename.strip()

    match = re.search(r'(PFS\d+)', clean_pdf_filename)
    if not match:
        return None
    
    pdf_invoice_num = match.group(1)
    
    for file in transaction_files:
        # Trim whitespace from the transaction filename and compare
        clean_tran_filename = file.name.strip()
        if pdf_invoice_num in clean_tran_filename and "INVOICE DETAILS" in clean_tran_filename.upper():
            return file
    return None

def main():
    """Defines the Streamlit UI and orchestrates the app flow."""
    st.set_page_config(page_title="Invoice Processor", layout="wide")
    st.title("🧾 Invoice and Transaction Processor")
    st.markdown("Upload invoice PDFs and their corresponding 'INVOICE DETAILS' transaction files. The tool will combine them into a final report.")

    if 'output_files' not in st.session_state:
        st.session_state.output_files = {}
    if 'processing_log' not in st.session_state:
        st.session_state.processing_log = []

    with st.sidebar:
        st.header("Configuration")
        api_key_input = st.text_input(
            "Enter your OpenAI API Key", type="password", help="Required for PDF data extraction."
        )
        st.header("Instructions")
        st.markdown("""
        1.  **Enter API Key**.
        2.  **Upload Invoice PDFs**.
        3.  **Upload Transaction Files**: These are the 'Upload file PFS... - INVOICE DETAILS' files.
        4.  **Process**: Click the button to start.
        5.  **Download**: Links for the final reports will appear below.
        """)
        
    invoice_pdfs = st.file_uploader(
        "1. Upload Invoice PDFs", type="pdf", accept_multiple_files=True
    )
    transaction_files = st.file_uploader(
        "2. Upload Corresponding Transaction Files (CSV, XLS, XLSX)",
        type=['csv', 'xls', 'xlsx'], accept_multiple_files=True
    )

    if st.button("Process Files", type="primary"):
        if not api_key_input:
            st.error("🚨 Please enter your OpenAI API key.")
        elif not invoice_pdfs or not transaction_files:
            st.warning("⚠️ Please upload at least one PDF and one transaction file.")
        else:
            st.session_state.output_files = {}
            st.session_state.processing_log = []
            
            with st.spinner("Processing... This may take a while."):
                progress_bar = st.progress(0)
                total_files = len(invoice_pdfs)

                for i, pdf_file in enumerate(invoice_pdfs):
                    log = st.session_state.processing_log
                    log.append(f"--- Processing: {pdf_file.name.strip()} ---")

                    matching_tran_file = find_matching_transaction_file(pdf_file.name, transaction_files)
                    
                    if not matching_tran_file:
                        log.append(f"⚠️ WARNING: No 'INVOICE DETAILS' file found for {pdf_file.name.strip()}. Skipping.")
                        continue
                    
                    log.append(f"✅ Matched with transaction file: {matching_tran_file.name.strip()}")

                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(pdf_file.getvalue())
                            pdf_path = tmp.name

                        log.append("Reading PDF and performing OCR...")
                        text = read_pdf(pdf_path) or ocr_pdf(pdf_path)
                        if not text: raise ValueError("Could not extract text from PDF.")
                        
                        log.append("Extracting summary data with AI...")
                        summary_data = extract_summary_data(text, api_key_input)
                        log.append(f" extracted: Date={summary_data.get('invoice_date')}, VAT={summary_data.get('vat_percentage')}%")

                        log.append("Processing transaction details...")
                        final_df = process_transactions(matching_tran_file, summary_data, text)
                        
                        output_filename = f"Final_Report_{os.path.splitext(pdf_file.name.strip())[0]}.xlsx"
                        excel_bytes = create_final_report(final_df)
                        st.session_state.output_files[output_filename] = excel_bytes
                        log.append(f"✅ Successfully generated report: {output_filename}")

                    except Exception as e:
                        logger.error(f"Failed to process {pdf_file.name.strip()}: {e}", exc_info=True)
                        log.append(f"❌ ERROR: {e}")
                    finally:
                        if 'pdf_path' in locals() and os.path.exists(pdf_path):
                            os.unlink(pdf_path)
                        progress_bar.progress((i + 1) / total_files)

    if st.session_state.output_files:
        st.header("✅ Processing Complete")
        st.subheader("Download Your Reports")
        for filename, file_bytes in st.session_state.output_files.items():
            st.download_button(
                label=f"Download {filename}",
                data=file_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    
    if st.session_state.processing_log:
        with st.expander("Show Processing Log"):
            st.code("\n".join(st.session_state.processing_log))

if __name__ == "__main__":
    main()
