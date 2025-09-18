from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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

    Args:
        llm_data: The JSON data extracted by the LLM.
        full_pdf_text: The complete text from the PDF for rule-based checks.

    Returns:
        An InvoiceData object.
    """
    # Extract values with fallbacks
    net_amount = float(llm_data.get("total_rent_net", 0.0))
    vat_percentage = float(llm_data.get("vat_percentage", 20.0)) # Default to 20% if not found
    vat_rate = vat_percentage / 100.0

    # Calculate gross amount
    gross_amount = round(net_amount * (1 + vat_rate), 2)

    # Business Logic: Determine product_code based on last page content
    # This logic is specific and fragile; an LLM could also infer this.
    product_code = "Unknown"
    if "LINE 1" in full_pdf_text: # A more robust check might involve analyzing the last 500 chars
        product_code = "Leasing"
    elif "LINE 2" in full_pdf_text:
        product_code = "GEN. EXP"
    
    # Parse date
    date_str = llm_data.get("invoice_date")
    invoice_date_obj = None
    if date_str:
        try:
            invoice_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            # Add fallback parsing if needed
            invoice_date_obj = None

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
