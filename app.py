# app.py (Corrected Version)

import streamlit as st
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, IO
import tempfile
import os
import logging
from datetime import datetime

# Import project modules
from extractor.pdf_reader import read_pdf
from extractor.ocr import ocr_pdf
from extractor.llm_client import extract_with_llm
from extractor.parser import parse_invoice, InvoiceData
from extractor.excel_writer import create_excel_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AppState:
    """A simple state object to hold results between runs."""
    processing_log: List[str] = list
    output_files: Dict[str, bytes] = dict
    error_messages: Dict[str, str] = dict

def get_state() -> AppState:
    """Gets the session state."""
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState(processing_log=[], output_files={}, error_messages={})
    return st.session_state.app_state

def process_files(invoice_files: List[IO[bytes]], transaction_file: Optional[IO[bytes]], api_key: str):
    """
    Main processing logic to extract data from invoices and generate reports.
    """
    state = get_state()
    state.processing_log = []
    state.output_files = {}
    state.error_messages = {}

    if not invoice_files:
        st.warning("Please upload at least one invoice PDF.")
        return

    # --- MODIFIED SECTION START ---
    # Read transaction data if available, handling CSV, XLS, and XLSX
    transaction_df = None
    if transaction_file:
        try:
            file_extension = os.path.splitext(transaction_file.name)[1].lower()
            if file_extension == '.csv':
                transaction_df = pd.read_csv(transaction_file)
            elif file_extension in ['.xls', '.xlsx']:
                # pd.read_excel can handle both old and new Excel formats
                transaction_df = pd.read_excel(transaction_file)
            else:
                st.error(f"Unsupported transaction file format: {file_extension}")
                return
            state.processing_log.append(f"Successfully loaded transaction file: {transaction_file.name}")
        except Exception as e:
            st.error(f"Error reading transaction file: {e}")
            logger.error(f"Failed to read transaction file {transaction_file.name}: {e}", exc_info=True)
            return
    # --- MODIFIED SECTION END ---


    progress_bar = st.progress(0)
    total_files = len(invoice_files)

    for i, uploaded_file in enumerate(invoice_files):
        filename = uploaded_file.name
        state.processing_log.append(f"--- Processing: {filename} ---")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                file_path = tmp.name

            text = read_pdf(file_path)
            if not text or len(text.strip()) < 100:
                state.processing_log.append("PDF appears to be a scan, applying OCR...")
                text = ocr_pdf(file_path)

            if not text:
                raise ValueError("Could not extract any text from the PDF.")

            state.processing_log.append("Extracting data using AI...")
            llm_response = extract_with_llm(text, api_key=api_key)
            state.processing_log.append(f"AI extraction confidence: {llm_response.get('confidence', 'N/A')}")

            state.processing_log.append("Applying business logic and formatting...")
            invoice_data = parse_invoice(llm_response, text)

            if transaction_df is not None:
                # Ensure the 'INVOICE' column exists before trying to access it
                if 'INVOICE' in transaction_df.columns:
                    match = transaction_df[transaction_df['INVOICE'] == invoice_data.invoice_number]
                    if not match.empty:
                        state.processing_log.append(f"✅ Found matching record for invoice {invoice_data.invoice_number} in transactions file.")
                    else:
                        state.processing_log.append(f"⚠️ WARNING: No matching record found for invoice {invoice_data.invoice_number} in transactions file.")
                else:
                    state.processing_log.append("⚠️ WARNING: 'INVOICE' column not found in the transaction file. Skipping cross-check.")

            output_filename = f"output_{os.path.splitext(filename)[0]}.xlsx"
            excel_bytes = create_excel_report(invoice_data)
            state.output_files[output_filename] = excel_bytes
            state.processing_log.append(f"✅ Successfully generated report: {output_filename}")

        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}", exc_info=True)
            state.error_messages[filename] = str(e)
            state.processing_log.append(f"❌ ERROR processing {filename}: {e}")

        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.unlink(file_path)
            progress_bar.progress((i + 1) / total_files)

def main():
    """Defines the Streamlit UI and orchestrates the app flow."""
    st.set_page_config(page_title="Invoice Processor", layout="wide")
    st.title("🧾 Invoice Processing and Reporting Tool")
    st.markdown("Upload your invoice PDFs and a single transaction file (CSV, XLS, or XLSX). The tool will extract key data, apply business logic, and generate a formatted Excel report for each invoice.")

    state = get_state()

    with st.sidebar:
        st.header("Configuration")
        api_key_input = st.text_input(
            "Enter your OpenAI API Key",
            type="password",
            help="Your API key is not stored. It is only used for the current session."
        )

        st.header("Instructions")
        st.markdown("""
        1.  **Enter API Key**: Paste your OpenAI API key in the field above.
        2.  **Upload Invoices**: Select one or more PDF files.
        3.  **Upload Transactions**: Select the transaction file.
        4.  **Process**: Click the 'Process Invoices' button.
        5.  **Download**: Download links will appear below.
        """)

    invoice_files = st.file_uploader(
        "Upload Invoice PDFs", type="pdf", accept_multiple_files=True
    )

    # --- MODIFIED LINE ---
    # Allow multiple file types for the transaction file uploader
    transaction_file = st.file_uploader(
        "Upload Transaction File (CSV, XLS, XLSX)",
        type=['csv', 'xls', 'xlsx']
    )

    if st.button("Process Invoices", type="primary"):
        if not api_key_input:
            st.error("🚨 Please enter your OpenAI API key in the sidebar to continue.")
        else:
            with st.spinner("Processing files... This may take a moment."):
                process_files(invoice_files, transaction_file, api_key=api_key_input)

    if state.output_files or state.error_messages:
        st.header("Processing Results")

        if state.output_files:
            st.subheader("Generated Reports")
            for filename, file_bytes in state.output_files.items():
                st.download_button(
                    label=f"Download {filename}",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        if state.error_messages:
            st.subheader("Errors Encountered")
            for filename, error in state.error_messages.items():
                st.error(f"**{filename}**: {error}")

        with st.expander("Show Processing Log"):
            st.code("\n".join(state.processing_log))

if __name__ == "__main__":
    main()
