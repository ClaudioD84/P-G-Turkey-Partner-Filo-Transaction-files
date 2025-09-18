# extractor/parser.py (New Robust Version)

import pandas as pd
import os
from typing import Dict, IO, List, Optional
from dateutil import parser as dateparser

def find_column(columns: List[str], keywords: List[str]) -> Optional[str]:
    """Helper function to find the first column name that contains any of the given keywords."""
    for col in columns:
        col_upper = str(col).upper()
        if any(key in col_upper for key in keywords):
            return col
    return None

def process_transactions(transaction_file: IO[bytes], summary_data: Dict, pdf_text: str) -> pd.DataFrame:
    """
    Reads a transaction file, enriches it with summary data from a PDF,
    and formats it into the final report structure.
    """
    file_extension = os.path.splitext(transaction_file.name)[1].lower()
    df = pd.read_csv(transaction_file) if file_extension == '.csv' else pd.read_excel(transaction_file)

    # --- Robust Column Finding ---
    # Find column names using a list of possible keywords.
    plate_col = find_column(df.columns, ['PLATE', 'PLAKA'])
    brand_col = find_column(df.columns, ['BRAND', 'MODEL'])
    # The amount column has different names in different files ('TOTAL RENT' vs 'TOTAL AMOUNT')
    amount_col = find_column(df.columns, ['TOTAL RENT', 'TOTAL AMOUNT'])

    # Raise a clear error if essential columns are not found
    if not all([plate_col, brand_col, amount_col]):
        missing = [col for col, name in [('Plate', plate_col), ('Brand', brand_col), ('Amount', amount_col)] if not name]
        raise ValueError(f"Could not find required columns in {transaction_file.name}: {', '.join(missing)}")

    # Select and rename the columns we found
    df = df[[plate_col, brand_col, amount_col]].rename(columns={
        plate_col: 'PLAKA',
        brand_col: 'RENTAL VEHICLE BRAND AND MODEL',
        amount_col: 'toplam ft.tutari'
    })

    # --- Data Enrichment from PDF ---
    vat_raw = summary_data.get('vat_percentage')
    vat_rate = (float(vat_raw) / 100.0) if vat_raw is not None else 0.20 # Default

    date_str = summary_data.get('invoice_date')
    invoice_date = dateparser.parse(date_str).strftime('%d.%m.%Y') if date_str else None

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
