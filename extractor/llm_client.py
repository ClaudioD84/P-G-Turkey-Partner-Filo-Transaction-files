# extractor/llm_client.py (Final, High-Accuracy Version)

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

    # --- NEW "SUPER-PROMPT" TAILORED FOR TURKISH INVOICES ---
    prompt = f"""
    You are a world-class data extraction expert specializing in Turkish financial documents.
    The following text is from a scanned invoice from "PARTNER FİLO ÇÖZÜMLERİ A.Ş." that has been processed by OCR. The text is very messy and contains many errors.
    Your task is to meticulously analyze the text to find and extract the key values into a perfect JSON object.

    **CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:**

    1.  **Find the Grand Total (Net Amount)**: This is the most important value.
        * Look for a summary table near the end of the document.
        * Search for Turkish keywords like **"ARA TOPLAM"** (Subtotal), **"TOPLAM"** (Total), or **"GENEL TOPLAM"** (Grand Total).
        * The value will be a number like **"3.450.961,18"**. You MUST parse this as **3450961.18**. Ignore the dots and use the comma as the decimal point. This is the **`total_rent_net`**.

    2.  **Find the VAT (KDV)**:
        * Look for the term **"HESAPLANAN KDV %20"** or a similar percentage.
        * The value next to it is the VAT amount. You need to extract the **percentage** itself (e.g., 20). This is the **`vat_percentage`**.

    3.  **Find the Invoice Number**:
        * Look for a unique ID, often labeled **"ETTN"**. It's a long alphanumeric string with dashes. Example: "C66DD4EC-3810-4803-8228-74178859FBA4". This is the **`invoice_number`**.
        * If ETTN is not clear, look for "FATURA NO".

    4.  **Find the Plate Number**:
        * The invoices list many vehicles. Do not extract a plate number, as there is no single one. Return **null** for the **`plate`** and **`car_brand`** fields.

    5.  **Return JSON**: Your output MUST be a valid JSON object. If you cannot find a value, you MUST return `null`, not an empty string.

    **EXAMPLE OF ANALYSIS:**
    If you see text like:
    `ARA TOPLAM 3.450.961,18`
    `HESAPLANAN KDV %20 690.192,24`
    `GENEL TOPLAM 4.141.153,42`
    
    Your JSON output should contain:
    `"total_rent_net": 3450961.18,`
    `"vat_percentage": 20.0,`

    --- OCR TEXT TO ANALYZE ---
    {text[:8000]}
    --- END TEXT ---

    Please provide the final JSON output.
    """

    try:
        # Switch to a more powerful model for better accuracy on difficult documents
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
