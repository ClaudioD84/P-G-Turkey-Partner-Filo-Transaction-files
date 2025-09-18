# extractor/llm_client.py

import openai
import json
import logging

logger = logging.getLogger(__name__)

def extract_summary_data(text: str, api_key: str) -> dict:
    """
    Extracts only the high-level summary data (Invoice #, Date, VAT) from the invoice text.
    """
    openai.api_key = api_key
    
    prompt = f"""
    You are a data extraction specialist. From the provided OCR text of a Turkish invoice,
    extract ONLY the following three fields and return them in a JSON object.

    1.  **invoice_number**: Find the number that looks like "PFS...". For example, "PFS2025000001235".
    2.  **invoice_date**: Find the date, usually labeled "Tarih". It will be in DD.MM.YYYY format. Reformat it to YYYY-MM-DD.
    3.  **vat_percentage**: Find the main VAT rate, usually labeled "HESAPLANAN KDV". Extract the number (e.g., 20 or 10).

    --- OCR TEXT ---
    {text[:4000]}
    --- END TEXT ---

    JSON Output:
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        content = response.choices[0].message.content
        logger.info(f"LLM Summary Response: {content}")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error during LLM call for summary data: {e}")
        raise RuntimeError(f"Failed to extract summary data from PDF: {e}")
