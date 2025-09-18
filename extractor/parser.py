# extractor/parser.py (Final Version with Automatic Header Detection)

import pandas as pd
import os
from typing import Dict, IO, List, Optional
from dateutil import parser as dateparser

def find_header_row(file: IO[bytes], keywords: List[str]) -> int:
    """Reads the first few lines of a file to find the correct header row number."""
    df_preview = pd.read_excel(file, header=None, nrows=10) if file.name.endswith(('.xls', '.xlsx')) else pd.read_csv(file, header=None, nrows=10)
    for index, row in df_preview.iterrows():
        row_str = ' '.join(str(x).upper() for x in row.dropna())
        if any(key.upper() in row_str for key in keywords):
            file.seek(0) # Reset file pointer after reading
            return index
    file.seek(0) # Reset file pointer if nothing is found
    raise ValueError("Could not find a valid header row containing keywords like 'PLATE' or 'PLAKA'.")

def find_column(columns: List[str], keywords: List[str]) -> Optional[str]:
    """Helper function to find a column name that contains any of the given keywords."""
    for col in columns:
        if any(key.upper() in str(col).upper() for key in keywords):
            return col
    return None

def process_transactions(transaction_file: IO[bytes], summary_data: Dict, pdf_text: str) -> pd.DataFrame:
    """
    Reads a transaction file, enriches it with summary data from a PDF,
    and formats it into the final report structure.
    """
    # --- NEW: Automatically find the header row ---
    header_row_index = find_header_row(transaction_file, ['PLATE', 'PLAKA'])
    
    # Read the file again, starting from the correct header
    file_extension = os.path.splitext(transaction_file.name)[1].lower()
    df = pd.read_csv(transaction_file, header=header_row_index) if file_extension == '.csv' else pd.read_excel(transaction_file, header=header_row_index)

    # --- Robust Column Finding ---
    plate_col = find_column(df.columns, ['PLATE', 'PLAKA'])
    brand_col = find_column(df.columns, ['BRAND', 'MODEL'])
    amount_col = find_column(df.columns, ['TOTAL RENT', 'TOTAL AMOUNT'])

    if not all([plate_col, brand_col, amount_col]):
        missing = [col for col, name in [('Plate', plate_col), ('Brand', brand_col), ('Amount', amount_col)] if not name]
        raise ValueError(f"Could not find required columns in {transaction_file.name}: {', '.join(missing)}")

    df = df[[plate_col, brand_col, amount_col]].rename(columns={
        plate_col: 'PLAKA',
        brand_col: 'RENTAL VEHICLE BRAND AND MODEL',
        amount_col: 'toplam ft.tutari'
    })

    # --- Data Enrichment & Calculation ---
    vat_raw = summary_data.get('vat_percentage')
    vat_rate = (float(vat_raw) / 100.0) if vat_raw is not None else 0.20

    date_str = summary_data.get('invoice_date')
    invoice_date = dateparser.parse(date_str).strftime('%d.%m.%Y') if date_str else None

    description = "leasing" if "LINE 1" in pdf_text else "GEN.EXP"

    df['GROSS'] = df['toplam ft.tutari'] * (1 + vat_rate)
    df['DATE'] = invoice_date
    df['DESCTRIPTION'] = description
    df['INVOICE'] = summary_data.get('invoice_number')

    final_columns = [
        'PLAKA', 'RENTAL VEHICLE BRAND AND MODEL', 'toplam ft.tutari',
        'GROSS', 'DATE', 'DESCTRIPTION', 'INVOICE'
    ]
    df = df[final_columns]

    return df
