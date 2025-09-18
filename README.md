# P-G-Turkey-Partner-Filo-Transaction-files# Streamlit Invoice Parser for Leasing Companies

This Streamlit application automates the process of parsing PDF invoices from leasing companies like Partner Filo Çözümleri. It extracts key invoice data, allows for optional integration with a vendor transaction file, and generates a formatted upload file for a core system.

## Key Business Rules & Parser Logic

The application is built around a few core business rules derived from the invoice structure:

1.  **Product Code Determination**: The parser determines the `ProductCode` by scanning the last page of each PDF for specific keywords:
    * If the text `(Line-1)` is found, the `ProductCode` is set to **"Leasing"**.
    * If the text `(Line-2)` is found, the `ProductCode` is set to **"GEN. EXP"**.

2.  **Financial Data**: The application extracts the main financial totals from the invoice summary, not the individual line items.
    * **Net Amount**: Pulled from the `Malzeme/Hizmet Toplam Tutan` (Subtotal) field.
    * **VAT Rate**: Detected from the `Hesaplanan KDV (%X)` field (e.g., 20% or 10%).
    * **Gross Amount**: Calculated as `Net Amount * (1 + VAT Rate)`. The total from the PDF (`Ödenecek Tutar`) is used for verification.

3.  **Vendor File Integration**: If a vendor transaction file (Excel/CSV) is provided, it can be used to enrich the data. However, the primary financial data (Net/VAT) is always sourced from the PDF to ensure accuracy. The current implementation focuses on the PDF-first approach as it contains all necessary information.

## How to Run the App

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Streamlit**:
    ```bash
    streamlit run app.py
    ```

3.  **Usage**:
    * Upload one or more PDF invoices using the file uploader.
    * Click the "Parse Invoices" button.
    * Review the parsed data in the preview table. You can edit any field directly in the table.
    * If any invoices fail to parse, a downloadable error report will be available.
    * Once you are satisfied with the data, click "Generate Upload File".
    * Download links for the final `UPLOAD.csv` and `UPLOAD_{...}.JUN` files will appear.

## Deployment to Streamlit Cloud

1.  Create a GitHub repository with `app.py`, `requirements.txt`, and any other necessary modules (like `parser.py`).
2.  Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
3.  Click "Deploy an app" and select the repository and branch.
4.  Ensure the main file path is set to `app.py`.
5.  Deploy the app.
