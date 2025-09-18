# extractor/ocr.py

import pytesseract
from PIL import Image
import pdfplumber
import logging

logger = logging.getLogger(__name__)

def ocr_pdf(file_path: str) -> str:
    """
    Performs OCR on each page of a PDF file. This is used for
    scanned documents where text extraction is not possible.

    Args:
        file_path: The local path to the scanned PDF file.

    Returns:
        The OCR-extracted text from the PDF as a single string.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # Convert PDF page to a high-resolution image
                img = page.to_image(resolution=300).original
                
                # Use Tesseract to do OCR on the image
                page_text = pytesseract.image_to_string(img, lang='eng') # Specify language if known
                if page_text:
                    text += page_text + "\n--- PAGE BREAK ---\n"
        logger.info(f"Successfully performed OCR on {file_path}")
        return text
    except Exception as e:
        logger.error(f"OCR failed for file {file_path}: {e}")
        # Depending on the error, you might need to check if Tesseract is installed
        # and available in the system's PATH.
        raise RuntimeError(f"OCR processing failed. Ensure Tesseract is correctly installed. Error: {e}")
