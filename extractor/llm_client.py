# extractor/llm_client.py (Improved AI Prompt)

import openai
import json
import logging

logger = logging.getLogger(__name__)

def extract_with_llm(text: str, api_key: str) -> dict:
    """
    Uses an LLM to extract structured data from invoice text.
    The prompt is optimized to handle messy OCR output.
    """
    if not api_key:
        raise ValueError("OpenAI API key not provided. Please enter it in the sidebar.")
    
    openai.api_key = api_key

    # --- NEW, MORE ROBUST PROMPT ---
    prompt = f"""
    You are an expert financial data extraction assistant. The following text is from an invoice,
    processed by Optical Character Recognition (OCR), so it may contain formatting errors or typos.
    Your task is to analyze the text and extract the key fields as a valid JSON object.

    Key Instructions:
    1.  **Invoice Number**: Look for terms like 'FATURA NO', 'Invoice No', 'ETTN', or a unique identifier.
    2.  **Invoice Date**: Find a date, often near the invoice number. Format it as YYYY-MM-DD.
    3.  **Plate**: Find a vehicle license plate, it will be a string with letters and numbers (e.g., '34-KVN-771').
    4.  **Total Net Amount**: Critically important. Look for a final total before tax. Search for keywords like 'TOPLAM', 'Total', 'Net Amount', 'TUTARI'. This MUST be a number.
    5.  **VAT Percentage**: Look for a tax rate like '20%', '10%', 'KDV'. Extract only the number.

    If a field is not found or you are unsure, the value MUST be null.

    --- OCR TEXT ---
    {text[:4000]}
    --- END TEXT ---

    JSON Output:
    {{
      "invoice_number": "...",
      "invoice_date": "YYYY-MM-DD",
      "plate": "...",
      "car_brand": "...",
      "total_rent_net": <number_or_null>,
      "vat_percentage": <number_or_null>,
      "confidence": <your_confidence_from_0.0_to_1.0>
    }}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0, # Set to 0 for maximum fact-based extraction
        )
        content = response.choices[0].message.content
        logger.info(f"LLM Raw Response: {content}")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error during LLM call: {e}")
        if "AuthenticationError" in str(type(e)):
             raise RuntimeError("Invalid OpenAI API key provided. Please check your key and try again.")
        raise RuntimeError(f"Failed to communicate with the LLM: {e}")
