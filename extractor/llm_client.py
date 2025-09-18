import streamlit as st
import openai
import json
import logging

logger = logging.getLogger(__name__)

def extract_with_llm(text: str) -> dict:
    """
    Uses an LLM to extract structured data from invoice text.

    Args:
        text: The text from which to extract data.

    Returns:
        A dictionary of the extracted data.
    """
    try:
        openai.api_key = st.secrets["openai_api_key"]
    except (KeyError, FileNotFoundError):
        raise ValueError("OpenAI API key not found. Please configure .streamlit/secrets.toml")

    # This prompt is designed for structured JSON output. It clearly defines the
    # desired fields and provides examples of expected formats (e.g., YYYY-MM-DD).
    # Requesting JSON helps in reliable parsing of the LLM's response.
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
            model="gpt-3.5-turbo-1106",  # A model that is good with JSON mode
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1, # Low temperature for factual extraction
        )
        content = response.choices[0].message.content
        logger.info(f"LLM Raw Response: {content}")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error during LLM call: {e}")
        raise RuntimeError(f"Failed to communicate with the LLM: {e}")
