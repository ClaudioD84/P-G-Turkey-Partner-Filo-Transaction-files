# extractor/excel_writer.py

import pandas as pd
import io

def create_final_report(df: pd.DataFrame) -> bytes:
    """
    Writes the final processed DataFrame to a formatted Excel file in memory.
    """
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
        
        workbook  = writer.book
        worksheet = writer.sheets['Transactions']

        # Define formats
        header_format = workbook.add_format({
            'bold': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1
        })
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        
        # Write headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Set column widths and formats
        worksheet.set_column('A:A', 15)  # PLAKA
        worksheet.set_column('B:B', 40)  # RENTAL VEHICLE BRAND AND MODEL
        worksheet.set_column('C:D', 18, currency_format) # toplam ft.tutari, GROSS
        worksheet.set_column('E:G', 25) # DATE, DESCTRIPTION, INVOICE

    return output_buffer.getvalue()
