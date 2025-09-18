# extractor/pdf_reader.py

import pdfplumber
import logging

logger = logging.getLogger(__name__)

def read_pdf(file_path: str) -> str:
    """
    Extracts all text from a given PDF file.

    Args:
        file_path: The local path to the PDF file.

    Returns:
        The extracted text from the PDF as a single string.
        Returns an empty string if the file cannot be opened.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n--- PAGE BREAK ---\n"
        logger.info(f"Successfully extracted text from {file_path}")
        return text
    except Exception as e:
        logger.error(f"Could not read PDF file at {file_path}: {e}")
        return ""
