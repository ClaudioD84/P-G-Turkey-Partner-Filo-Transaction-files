import pytest
from extractor.parser import parse_invoice, InvoiceData
from datetime import datetime

@pytest.fixture
def mock_llm_data():
    """Provides a sample LLM response for testing."""
    return {
        "invoice_number": "PFS2025000001235",
        "invoice_date": "2025-06-01",
        "plate": "34-KVN-771",
        "car_brand": "MERCEDES-BENZ A 200 SEDAN",
        "total_rent_net": 36885.00,
        "vat_percentage": 20.0,
        "confidence": 0.95
    }

@pytest.fixture
def mock_pdf_text():
    """Provides sample PDF text with business rule keywords."""
    return "Some random invoice text... and on the last page: LINE 1 leasing info."

def test_parse_invoice_leasing(mock_llm_data, mock_pdf_text):
    """Tests the parsing logic for a 'Leasing' product code."""
    parsed_data = parse_invoice(mock_llm_data, mock_pdf_text)

    assert isinstance(parsed_data, InvoiceData)
    assert parsed_data.invoice_number == "PFS2025000001235"
    assert parsed_data.invoice_date == datetime(2025, 6, 1)
    assert parsed_data.net_amount == 36885.00
    assert parsed_data.vat_rate == 0.20
    assert parsed_data.gross_amount == pytest.approx(44262.00)
    assert parsed_data.product_code == "Leasing"

def test_parse_invoice_gen_exp(mock_llm_data):
    """Tests the parsing logic for a 'GEN. EXP' product code."""
    pdf_text_gen_exp = "Text with LINE 2 on the final page."
    parsed_data = parse_invoice(mock_llm_data, pdf_text_gen_exp)
    assert parsed_data.product_code == "GEN. EXP"

def test_parse_invoice_missing_data(mock_pdf_text):
    """Tests behavior with incomplete LLM data."""
    incomplete_llm_data = {
        "invoice_number": "INV-002",
        "total_rent_net": 500.0
    }
    parsed_data = parse_invoice(incomplete_llm_data, mock_pdf_text)
    
    assert parsed_data.net_amount == 500.0
    assert parsed_data.vat_rate == 0.20  # Falls back to default
    assert parsed_data.gross_amount == pytest.approx(600.00)
    assert parsed_data.plate == "N/A"
