# extractor/ocr.py

import pytesseract
from PIL import Image
import pdfplumber
import logging

logger = logging.getLogger(__name__)

def ocr_pdf(file_path: str) -> str:
    """
    Performs OCR on each page of a PDF file.
    This relies on Tesseract being installed in the environment's PATH.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                img = page.to_image(resolution=300).original
                
                # Use Tesseract to find and read text in the image
                page_text = pytesseract.image_to_string(img, lang='eng')
                if page_text:
                    text += page_text + "\n--- PAGE BREAK ---\n"
        logger.info(f"Successfully performed OCR on {file_path}")
        return text
    except pytesseract.TesseractNotFoundError:
        # This error now correctly indicates a build/environment problem
        logger.error("Tesseract command not found. Ensure 'tesseract-ocr' is in your packages.txt file.")
        raise RuntimeError("OCR Error: Tesseract is not installed in the app environment. Please add it to packages.txt.")
    except Exception as e:
        logger.error(f"An unexpected OCR error occurred for file {file_path}: {e}")
        raise RuntimeError(f"An unexpected OCR processing error occurred: {e}")
