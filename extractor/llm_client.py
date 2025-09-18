# extractor/llm_client.py (Final Version)

import openai
import json
import logging

logger = logging.getLogger(__name__)

def extract_with_llm(text: str, api_key: str) -> dict:
    """
    Uses a powerful LLM with a highly specific prompt to extract data
    from messy OCR text of Turkish invoices.
    """
    if not api_key:
        raise ValueError("OpenAI API key not provided. Please enter it in the sidebar.")
    
    openai.api_key = api_key

    # --- FINAL PROMPT WITH ENHANCED DATE & VAT INSTRUCTIONS ---
    prompt = f"""
    You are an expert financial data extraction assistant for Turkish invoices from "PARTNER FİLO ÇÖZÜMLERİ A.Ş.".
    The following text is from a scanned invoice processed by OCR and is very messy.
    Your task is to analyze the text and extract the key fields into a perfect JSON object.

    **CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:**

    1.  **Invoice Date (Tarih)**:
        * Find the date, which is usually on the first page. Look for the Turkish word **"Tarih"**.
        * The format will likely be DD.MM.YYYY (e.g., 05.06.2025).
        * You MUST reformat it to **YYYY-MM-DD** in your output. This is the **`invoice_date`**.

    2.  **Invoice Number (ETTN)**:
        * Find the **"ETTN"**. It's a long alphanumeric string with dashes. This is the **`invoice_number`**.

    3.  **Grand Total (Net Amount)**:
        * Look for a summary table near the end. Search for **"ARA TOPLAM"** (Subtotal) or **"TOPLAM"**.
        * The value will be a number like **"3.450.961,18"**. You MUST parse this as **3450961.18** (ignore dots, use comma as decimal). This is the **`total_rent_net`**.

    4.  **VAT Percentage (KDV)**:
        * Look for **"HESAPLANAN KDV %20"** or a similar percentage.
        * Extract the percentage number (e.g., 20 or 10). This is the **`vat_percentage`**.

    5.  **Plate Number**:
        * The invoices list many vehicles. Return **null** for the **`plate`** and **`car_brand`** fields.

    6.  **JSON Output**: If a value cannot be found, it MUST be `null`.

    --- OCR TEXT TO ANALYZE ---
    {text[:8000]}
    --- END TEXT ---

    Please provide the final JSON output.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        content = response.choices[0].message.content
        logger.info(f"LLM Raw Response: {content}")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error during LLM call: {e}")
        if "AuthenticationError" in str(type(e)):
             raise RuntimeError("Invalid OpenAI API key provided. Please check your key and try again.")
        raise RuntimeError(f"Failed to communicate with the LLM: {e}")
