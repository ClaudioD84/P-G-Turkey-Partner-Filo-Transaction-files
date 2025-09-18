# extractor/parser.py

import pandas as pd
import os
from typing import Dict, IO
from dateutil import parser as dateparser

def process_transactions(transaction_file: IO[bytes], summary_data: Dict, pdf_text: str) -> pd.DataFrame:
    """
    Reads a transaction file, enriches it with summary data from a PDF,
    and formats it into the final report structure.
    """
    # Read the transaction file (CSV, XLS, or XLSX) into a DataFrame
    file_extension = os.path.splitext(transaction_file.name)[1].lower()
    if file_extension == '.csv':
        df = pd.read_csv(transaction_file)
    else:
        df = pd.read_excel(transaction_file)

    # --- Data Cleaning and Column Mapping ---
    # The column names can be inconsistent. We find them by keywords.
    # This makes the script robust to small changes in the input files.
    column_map = {
        'PLAKA': [col for col in df.columns if 'PLATE' in col.upper()][0],
        'RENTAL VEHICLE BRAND AND MODEL': [col for col in df.columns if 'BRAND' in col.upper()][0],
        'toplam ft.tutari': [col for col in df.columns if 'RENT' in col.upper() and 'TOTAL' in col.upper()][0]
    }
    
    # Select and rename columns to match the target format
    df = df[list(column_map.values())].rename(columns={v: k for k, v in column_map.items()})

    # --- Data Enrichment from PDF ---
    # Get VAT rate and Invoice Date from the summary data extracted by the LLM
    vat_raw = summary_data.get('vat_percentage')
    vat_rate = (float(vat_raw) / 100.0) if vat_raw is not None else 0.20 # Default to 20%

    date_str = summary_data.get('invoice_date')
    invoice_date = dateparser.parse(date_str).strftime('%d.%m.%Y') if date_str else None

    # Get description/product code from the PDF text
    description = "leasing" if "LINE 1" in pdf_text else "GEN.EXP"

    # Add new columns
    df['GROSS'] = df['toplam ft.tutari'] * (1 + vat_rate)
    df['DATE'] = invoice_date
    df['DESCTRIPTION'] = description
    df['INVOICE'] = summary_data.get('invoice_number')

    # Ensure correct column order
    final_columns = [
        'PLAKA', 'RENTAL VEHICLE BRAND AND MODEL', 'toplam ft.tutari', 
        'GROSS', 'DATE', 'DESCTRIPTION', 'INVOICE'
    ]
    df = df[final_columns]

    return df
