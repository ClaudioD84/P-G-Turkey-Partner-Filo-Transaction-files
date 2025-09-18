# Invoice Processing Tool

This tool automates the extraction of data from PDF invoices, cross-references it with a transaction file, and generates structured Excel reports.

## Features

- Extracts data from text-based and scanned PDF invoices.
- Uses a Large Language Model (LLM) for intelligent data extraction.
- Cross-references invoice data with a transaction CSV file.
- Generates one formatted Excel file per invoice.
- Supports both Dropbox and local file system as input sources.
- Logs extraction details and potential discrepancies.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/invoice-processing-tool.git](https://github.com/your-username/invoice-processing-tool.git)
    cd invoice-processing-tool
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Tesseract OCR:**
    Follow the installation instructions for your operating system from the [official Tesseract documentation](https.org/docs/).

5.  **Configure the application:**
    -   Rename `config.example.yml` to `config.yml`.
    -   Fill in your Dropbox API key, OpenAI API key, and other settings.

## Usage

The tool can be run from the command line with either a Dropbox folder path or a local directory path.

### Running with a Dropbox Folder

```bash
python run.py --source dropbox:/path/to/your/folder
