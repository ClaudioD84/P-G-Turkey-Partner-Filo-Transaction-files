import pandas as pd
import io
from .parser import InvoiceData
from dataclasses import asdict

def create_excel_report(data: InvoiceData) -> bytes:
    """
    Creates a formatted Excel report from the processed data in memory.

    Args:
        data: The processed InvoiceData object.

    Returns:
        A bytes object containing the Excel file content.
    """
    # Convert dataclass to a dictionary and wrap in a list for DataFrame creation
    data_dict = [asdict(data)]
    df = pd.DataFrame(data_dict)

    # Format date column if it exists and is not None
    if data.invoice_date:
        df['invoice_date'] = pd.to_datetime(df['invoice_date']).dt.strftime('%d/%m/%Y')
    else:
        df['invoice_date'] = 'N/A'

    # Reorder and rename columns to match the required template
    column_map = {
        'invoice_number': 'Invoice Number',
        'invoice_date': 'Invoice Date',
        'plate': 'Plate',
        'car_brand': 'Car Brand',
        'product_code': 'Product Code',
        'net_amount': 'Net Amount',
        'vat_rate': 'VAT Rate',
        'gross_amount': 'Gross Amount'
    }
    df = df[column_map.keys()].rename(columns=column_map)
    
    # Create an in-memory Excel file
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Invoice Details')
        
        workbook  = writer.book
        worksheet = writer.sheets['Invoice Details']

        # Define formats
        header_format = workbook.add_format({
            'bold': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1
        })
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        percent_format = workbook.add_format({'num_format': '0.0%', 'border': 1})
        default_format = workbook.add_format({'border': 1})
        
        # Write headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Apply formatting to columns
        worksheet.set_column('A:E', 20, default_format) # Invoice Num, Date, Plate, Brand, Code
        worksheet.set_column('F:F', 15, currency_format) # Net Amount
        worksheet.set_column('G:G', 12, percent_format)  # VAT Rate
        worksheet.set_column('H:H', 15, currency_format) # Gross Amount

    return output_buffer.getvalue()
