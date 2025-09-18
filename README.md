# Invoice Processing Streamlit App

This tool provides a web interface to automate the extraction of data from PDF invoices, cross-reference it with a transaction file, and generate structured Excel reports.

## Features

-   **Web-Based UI**: Easy-to-use interface powered by Streamlit for uploading files.
-   **Intelligent Extraction**: Extracts data from both text-based and scanned PDF invoices using OCR and a Large Language Model (LLM).
-   **Data Validation**: Cross-references invoice data with a transaction CSV file.
-   **Formatted Output**: Generates one downloadable Excel file per invoice, matching a predefined template.
-   **Secure**: Uses Streamlit's secrets management for API keys.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd invoice-processing-streamlit
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Tesseract OCR:**
    This is required for processing scanned (image-based) PDFs. Follow the installation instructions for your OS from the [official Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html).

5.  Run the App: Launch the application. You will be prompted to enter your OpenAI API key directly in the web interface.


## How to Run

Launch the Streamlit application from your terminal:

```bash
streamlit run app.py
