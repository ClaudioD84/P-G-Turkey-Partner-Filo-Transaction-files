# extractor/parser.py (Final Version)

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from dateutil import parser as dateparser # Using a more flexible date parser

@dataclass
class InvoiceData:
    """Represents the final, structured data for one invoice."""
    invoice_number: str
    invoice_date: Optional[datetime]
    plate: str
    car_brand: str
    product_code: str
    net_amount: float
    vat_rate: float
    gross_amount: float

def parse_invoice(llm_data: dict, full_pdf_text: str) -> InvoiceData:
    """
    Parses the data extracted by the LLM, applies business logic,
    and returns a structured InvoiceData object.
    """
    net_amount_raw = llm_data.get("total_rent_net")
    net_amount = float(net_amount_raw) if net_amount_raw is not None else 0.0

    vat_percentage_raw = llm_data.get("vat_percentage")
    vat_percentage = float(vat_percentage_raw) if vat_percentage_raw is not None else 20.0 # Default to 20%

    vat_rate = vat_percentage / 100.0
    gross_amount = round(net_amount * (1 + vat_rate), 2)

    product_code = "Unknown"
    if "LINE 1" in full_pdf_text:
        product_code = "Leasing"
    elif "LINE 2" in full_pdf_text:
        product_code = "GEN. EXP"
    
    # --- MODIFIED SECTION START ---
    # Use a more flexible date parser to handle various formats
    date_str = llm_data.get("invoice_date")
    invoice_date_obj = None
    if date_str:
        try:
            # dateutil.parser can intelligently handle most date formats
            invoice_date_obj = dateparser.parse(date_str)
        except (ValueError, TypeError):
            invoice_date_obj = None
    # --- MODIFIED SECTION END ---

    return InvoiceData(
        invoice_number=llm_data.get("invoice_number", "N/A"),
        invoice_date=invoice_date_obj,
        plate=llm_data.get("plate", "N/A"),
        car_brand=llm_data.get("car_brand", "N/A"),
        net_amount=net_amount,
        vat_rate=vat_rate,
        gross_amount=gross_amount,
        product_code=product_code,
    )
