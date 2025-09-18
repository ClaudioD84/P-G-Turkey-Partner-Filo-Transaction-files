# extractor/ocr.py

import pytesseract
from PIL import Image
import pdfplumber
import logging
import platform

logger = logging.getLogger(__name__)

# --- Tesseract Command Path Configuration ---
# If you are still getting errors after installing Tesseract,
# tell the script EXACTLY where to find the executable file.

# 1. Find the path to your Tesseract installation.
# 2. Uncomment the line for your operating system and paste the path.
#    Make sure the path string starts with an 'r' (e.g., r"C:\...")

# Example for Windows:
# tesseract_cmd_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Example for macOS (if installed with Homebrew on Apple Silicon):
# tesseract_cmd_path = r"/opt/homebrew/bin/tesseract"

# Example for Linux:
# tesseract_cmd_path = r"/usr/bin/tesseract"

# This block checks if you've defined the path and sets it for pytesseract
if 'tesseract_cmd_path' in locals():
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path


def ocr_pdf(file_path: str) -> str:
    """
    Performs OCR on each page of a PDF file.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                img = page.to_image(resolution=300).original
                
                page_text = pytesseract.image_to_string(img, lang='eng')
                if page_text:
                    text += page_text + "\n--- PAGE BREAK ---\n"
        logger.info(f"Successfully performed OCR on {file_path}")
        return text
    except pytesseract.TesseractNotFoundError as e:
        logger.error(f"Tesseract not found: {e}")
        raise RuntimeError("Tesseract is not installed or it's not in your PATH. See README file for more information.")
    except Exception as e:
        logger.error(f"OCR failed for file {file_path}: {e}")
        raise RuntimeError(f"OCR processing failed. Error: {e}")
