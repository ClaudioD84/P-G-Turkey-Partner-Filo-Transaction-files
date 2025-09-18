import pdfplumber
import re
import io
from decimal import Decimal, ROUND_HALF_UP

def clean_and_convert_decimal(text_value):
    """Cleans Turkish number format (dots for thousands, comma for decimal) and converts to Decimal."""
    if not text_value:
        return Decimal('0.00')
    # Remove thousands separators (.) and then replace decimal comma (,) with a dot (.)
    cleaned_text = text_value.replace('.', '').replace(',', '.')
    return Decimal(cleaned_text).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def parse_pdf_invoice(file_content, filename):
    """
    Parses the content of a single PDF invoice file.

    Args:
        file_content (bytes): The byte content of the PDF file.
        filename (str): The original name of the file for error reporting.

    Returns:
        A dictionary containing parsed invoice data or an error message.
    """
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

            # --- Regex patterns for data extraction ---
            invoice_no_pattern = re.compile(r"Fatura No:\s*([A-Z0-9]+)")
            invoice_date_pattern = re.compile(r"Fatura Tarihi:\s*(\d{2}-\d{2}-\d{4})")
            net_amount_pattern = re.compile(r"Malzeme/Hizmet Toplam Tutan\s*([\d\.,]+)\s*TL")
            vat_pattern = re.compile(r"KDV\s*\(%\s*(\d{1,2})\s*,\s*00\)")
            
            # --- Extract data ---
            invoice_no = invoice_no_pattern.search(full_text)
            invoice_date = invoice_date_pattern.search(full_text)
            net_amount = net_amount_pattern.search(full_text)
            vat = vat_pattern.search(full_text)

            # --- Determine Product Code based on Line-1 or Line-2 ---
            product_code = "UNKNOWN"
            if re.search(r"\(Line-1\)", full_text, re.IGNORECASE):
                product_code = "Leasing"
            elif re.search(r"\(Line-2\)", full_text, re.IGNORECASE):
                product_code = "GEN. EXP"

            # --- Assemble results ---
            parsed_data = {
                "filename": filename,
                "invoice_number": invoice_no.group(1) if invoice_no else None,
                "invoice_date": invoice_date.group(1) if invoice_date else None,
                "product_code": product_code,
                "net_amount": clean_and_convert_decimal(net_amount.group(1)) if net_amount else Decimal('0.00'),
                "vat_rate": Decimal(int(vat.group(1))) / Decimal(100) if vat else None,
            }
            
            # --- Validation ---
            if not all([parsed_data["invoice_number"], parsed_data["invoice_date"], parsed_data["net_amount"] is not None, parsed_data["vat_rate"] is not None]):
                raise ValueError("One or more critical fields could not be parsed.")

            return {"status": "success", "data": parsed_data}

    except Exception as e:
        return {
            "status": "error",
            "filename": filename,
            "reason": f"Failed to parse. Error: {str(e)}. Please check if the file is a valid Partner Fillo invoice."
        }
