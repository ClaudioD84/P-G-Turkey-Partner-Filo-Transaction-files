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

def process_files(invoice_files: List[IO[bytes]], transaction_file: Optional[IO[bytes]]):
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

    # Read transaction data if available
    transaction_df = None
    if transaction_file:
        transaction_df = pd.read_csv(transaction_file)
        state.processing_log.append(f"Successfully loaded transaction file: {transaction_file.name}")

    progress_bar = st.progress(0)
    total_files = len(invoice_files)

    for i, uploaded_file in enumerate(invoice_files):
        filename = uploaded_file.name
        state.processing_log.append(f"--- Processing: {filename} ---")
        try:
            # Save the uploaded file to a temporary location to get a stable path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                file_path = tmp.name

            # 1. Read PDF text (with OCR fallback)
            text = read_pdf(file_path)
            if not text or len(text.strip()) < 100:
                state.processing_log.append("PDF appears to be a scan, applying OCR...")
                text = ocr_pdf(file_path)
            
            if not text:
                raise ValueError("Could not extract any text from the PDF.")

            # 2. Use LLM to extract structured data
            state.processing_log.append("Extracting data using AI...")
            llm_response = extract_with_llm(text)
            state.processing_log.append(f"AI extraction confidence: {llm_response.get('confidence', 'N/A')}")
            
            # 3. Parse and apply business logic
            state.processing_log.append("Applying business logic and formatting...")
            invoice_data = parse_invoice(llm_response, text)

            # 4. Cross-check with transaction file (if provided)
            if transaction_df is not None:
                match = transaction_df[transaction_df['INVOICE'] == invoice_data.invoice_number]
                if not match.empty:
                    state.processing_log.append(f"✅ Found matching record for invoice {invoice_data.invoice_number} in transactions file.")
                else:
                    state.processing_log.append(f"⚠️ WARNING: No matching record found for invoice {invoice_data.invoice_number} in transactions file.")

            # 5. Generate Excel report in memory
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
                os.unlink(file_path) # Clean up temp file
            progress_bar.progress((i + 1) / total_files)

def main():
    """Defines the Streamlit UI and orchestrates the app flow."""
    st.set_page_config(page_title="Invoice Processor", layout="wide")
    st.title("🧾 Invoice Processing and Reporting Tool")
    st.markdown("Upload your invoice PDFs and a single transaction CSV file. The tool will extract key data, apply business logic, and generate a formatted Excel report for each invoice.")

    state = get_state()

    with st.sidebar:
        st.header("Configuration")
        st.info("API keys are securely managed via Streamlit secrets.")

        st.header("Instructions")
        st.markdown("""
        1.  **Upload Invoice PDFs**: Select one or more invoice files.
        2.  **Upload Transaction CSV**: Select the corresponding transaction file.
        3.  **Process**: Click the 'Process Invoices' button.
        4.  **Download**: Once processing is complete, download links for each Excel report will appear.
        """)
        
    # File Uploader
    invoice_files = st.file_uploader(
        "Upload Invoice PDFs", type="pdf", accept_multiple_files=True
    )
    transaction_file = st.file_uploader(
        "Upload Transaction CSV", type="csv"
    )

    if st.button("Process Invoices", type="primary"):
        with st.spinner("Processing files... This may take a moment."):
            process_files(invoice_files, transaction_file)
    
    # --- Display Results ---
    if state.output_files or state.error_messages:
        st.header("Processing Results")
        
        # Display successful outputs and download buttons
        if state.output_files:
            st.subheader("Generated Reports")
            for filename, file_bytes in state.output_files.items():
                st.download_button(
                    label=f"Download {filename}",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        
        # Display errors
        if state.error_messages:
            st.subheader("Errors Encountered")
            for filename, error in state.error_messages.items():
                st.error(f"**{filename}**: {error}")
        
        # Display log
        with st.expander("Show Processing Log"):
            st.code("\n".join(state.processing_log))

if __name__ == "__main__":
    # Check for API Key
    try:
        if not st.secrets["openai_api_key"]:
            st.error("OpenAI API key is not set. Please add it to your .streamlit/secrets.toml file.")
        else:
            main()
    except (FileNotFoundError, KeyError):
        st.error("OpenAI API key is missing. Please create and configure your .streamlit/secrets.toml file.")
