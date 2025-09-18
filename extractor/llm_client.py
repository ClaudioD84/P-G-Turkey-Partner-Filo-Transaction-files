# extractor/llm_client.py (Updated Version)

import openai
import json
import logging

logger = logging.getLogger(__name__)

def extract_with_llm(text: str, api_key: str) -> dict:
    """
    Uses an LLM to extract structured data from invoice text.

    Args:
        text: The text from which to extract data.
        api_key: The user-provided OpenAI API key.

    Returns:
        A dictionary of the extracted data.
    """
    if not api_key:
        raise ValueError("OpenAI API key not provided. Please enter it in the sidebar.")
    
    openai.api_key = api_key

    prompt = f"""
    You are an expert invoice data extraction assistant. Analyze the following invoice text
    and extract the specified fields. Return the result as a valid JSON object.

    Fields to extract:
    - "invoice_number": The invoice identifier string.
    - "invoice_date": The date of the invoice in YYYY-MM-DD format.
    - "plate": The vehicle license plate number.
    - "car_brand": The make and model of the car.
    - "total_rent_net": The net total rental amount (before tax). This should be a number.
    - "vat_percentage": The Value Added Tax percentage applied. This should be a number (e.g., 20 for 20%).
    - "confidence": Your confidence in the extraction accuracy, from 0.0 to 1.0.

    If a field is not found, return null for its value.

    --- INVOICE TEXT ---
    {text[:4000]}
    --- END TEXT ---

    JSON Output:
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        logger.info(f"LLM Raw Response: {content}")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error during LLM call: {e}")
        # Check for authentication errors specifically
        if "AuthenticationError" in str(type(e)):
             raise RuntimeError("Invalid OpenAI API key provided. Please check your key and try again.")
        raise RuntimeError(f"Failed to communicate with the LLM: {e}")
