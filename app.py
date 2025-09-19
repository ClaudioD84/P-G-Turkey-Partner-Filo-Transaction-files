# app.py (Corrected Version)

import streamlit as st
import pandas as pd
import tempfile
import os
import logging
import re
from typing import List, Optional, IO

# Import project modules
from extractor.pdf_reader import read_pdf
from extractor.ocr import ocr_pdf
from extractor.llm_client import extract_summary_data
from extractor.parser import process_transactions
from extractor.excel_writer import create_final_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_matching_transaction_file(pdf_filename: str, transaction_files: List[IO[bytes]]) -> Optional[IO[bytes]]:
    """
    Finds the best corresponding transaction file for a given PDF.
    It first tries to match using a number in parentheses (e.g., '(153351)').
    If that fails, it falls back to matching the 'PFS...' number.
    """
    clean_pdf_filename = pdf_filename.strip()
    
    # Primary strategy: Find number in parentheses, e.g., (153351)
    primary_match = re.search(r'\((\d+)\)', clean_pdf_filename)
    if primary_match:
        search_key = primary_match.group(1)
    else:
        # Fallback strategy: Find the PFS number
        fallback_match = re.search(r'(PFS\d+)', clean_pdf_filename)
        if not fallback_match:
            return None
        search_key = fallback_match.group(1)
        
    # Find all possible candidate files that contain the search key
    candidates = [file for file in transaction_files if search_key in file.name.strip()]
            
    if not candidates:
        return None
        
    # Prioritize the file with "INVOICE DETAILS" in the name
    for candidate in candidates:
        if "INVOICE DETAILS" in candidate.name.upper():
            return candidate
            
    # If no specific match, return the first candidate found
    return candidates[0]

def main():
    """Defines the Streamlit UI and orchestrates the app flow."""
    st.set_page_config(page_title="Invoice Processor", layout="wide")
    st.title("🧾 Invoice and Transaction Processor")
    st.markdown("Upload invoice PDFs and their corresponding transaction files. The tool will combine them into a final report.")

    # Initialize session state
    if 'output_files' not in st.session_state: st.session_state.output_files = {}
    if 'processing_log' not in st.session_state: st.session_state.processing_log = []

    with st.sidebar:
        st.header("Configuration")
        api_key_input = st.text_input("Enter your OpenAI API Key", type="password")
        st.header("Instructions")
        st.markdown("""
        1.  Enter API Key.
        2.  Upload Invoice PDFs.
        3.  Upload Transaction Files.
        4.  Process & Download.
        """)
        
    # --- CORRECTED LINES ---
    invoice_pdfs = st.file_uploader("1. Upload Invoice PDFs", type="pdf", accept_multiple_files=True)
    transaction_files = st.file_uploader("2. Upload Transaction Files (CSV, XLS, XLSX)", type=['csv', 'xls', 'xlsx'], accept_multiple_files=True)
    # --- END CORRECTION ---

    if st.button("Process Files", type="primary"):
        if not api_key_input: st.error("🚨 Please enter your OpenAI API key.")
        elif not invoice_pdfs or not transaction_files: st.warning("⚠️ Please upload at least one PDF and one transaction file.")
        else:
            st.session_state.output_files, st.session_state.processing_log = {}, []
            progress_bar = st.progress(0)

            for i, pdf_file in enumerate(invoice_pdfs):
                log = st.session_state.processing_log
                pdf_name = pdf_file.name.strip()
                log.append(f"--- Processing: {pdf_name} ---")

                matching_tran_file = find_matching_transaction_file(pdf_name, transaction_files)
                
                if not matching_tran_file:
                    log.append(f"⚠️ WARNING: No matching transaction file found for {pdf_name}. Skipping.")
                    continue
                
                log.append(f"✅ Matched with: {matching_tran_file.name.strip()}")

                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(pdf_file.getvalue())
                        pdf_path = tmp.name

                    log.append("Reading PDF...")
                    text = read_pdf(pdf_path) or ocr_pdf(pdf_path)
                    if not text: raise ValueError("Could not extract text from PDF.")
                    
                    log.append("Extracting summary with AI...")
                    summary_data = extract_summary_data(text, api_key_input)
                    log.append(f" extracted: Date={summary_data.get('invoice_date')}, VAT={summary_data.get('vat_percentage')}%")

                    log.append("Processing transaction details...")
                    final_df = process_transactions(matching_tran_file, summary_data, text)
                    
                    output_filename = f"Final_Report_{os.path.splitext(pdf_name)[0]}.xlsx"
                    excel_bytes = create_final_report(final_df)
                    st.session_state.output_files[output_filename] = excel_bytes
                    log.append(f"✅ Successfully generated report: {output_filename}")

                except Exception as e:
                    logger.error(f"Failed to process {pdf_name}: {e}", exc_info=True)
                    log.append(f"❌ ERROR: {e}")
                finally:
                    if 'pdf_path' in locals() and os.path.exists(pdf_path): os.unlink(pdf_path)
                    progress_bar.progress((i + 1) / len(invoice_pdfs))

    if st.session_state.output_files:
        st.header("✅ Processing Complete")
        for filename, file_bytes in st.session_state.output_files.items():
            st.download_button(
                label=f"Download {filename}", data=file_bytes, file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    
    if st.session_state.processing_log:
        with st.expander("Show Processing Log"): st.code("\n".join(st.session_state.processing_log))

if __name__ == "__main__":
    main()
