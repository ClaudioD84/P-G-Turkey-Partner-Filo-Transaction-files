import streamlit as st
import pandas as pd
import string
import random
from datetime import datetime
from decimal import Decimal

# Import the parsing function from our support module
from parser import parse_pdf_invoice

# --- Page Configuration ---
st.set_page_config(
    page_title="Invoice Parser",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- App State Management ---
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = pd.DataFrame()
if 'error_log' not in st.session_state:
    st.session_state.error_log = []
if 'edited_data' not in st.session_state:
    st.session_state.edited_data = pd.DataFrame()

# --- Helper Functions ---
def generate_random_suffix(length=6):
    """Generates a random alphanumeric string for filenames."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def build_upload_df(df):
    """Computes gross amounts and formats the DataFrame for final upload."""
    if df.empty:
        return df

    # Ensure correct types
    df['net_amount'] = df['net_amount'].apply(Decimal)
    df['vat_rate'] = df['vat_rate'].apply(Decimal)

    # Calculate gross amount
    df['gross_amount'] = df.apply(
        lambda row: (row['net_amount'] * (Decimal('1') + row['vat_rate'])).quantize(Decimal('0.01')),
        axis=1
    )

    # Define final column order and rename for export
    final_columns = {
        'invoice_number': 'InvoiceID',
        'invoice_date': 'Date',
        'product_code': 'ProductCode',
        'net_amount': 'NetAmount',
        'vat_rate': 'VATRate',
        'gross_amount': 'GrossAmount',
        'filename': 'SourceFile'
    }
    
    upload_df = df[final_columns.keys()].copy()
    upload_df.rename(columns=final_columns, inplace=True)
    return upload_df

# --- Sidebar ---
with st.sidebar:
    st.title("📄 Invoice Parser")
    st.info(
        "Upload Partner Fillo PDF invoices to parse them and generate a core system upload file."
    )
    
    st.header("Parsing Rules")
    st.markdown("""
    - **Leasing**: Detected if `(Line-1)` is present in the PDF.
    - **GEN. EXP**: Detected if `(Line-2)` is present in the PDF.
    - **VAT Rate**: Automatically detected as `10%` or `20%`.
    - **Net Amount**: Extracted from the subtotal line before VAT.
    """)
    
    st.warning("This app is designed for the specific format of 'Partner Filo Çözümleri' invoices.")

# --- Main Application UI ---
st.title("Invoice Processing Dashboard")

# --- File Uploader ---
st.header("1. Upload Files")
uploaded_files = st.file_uploader(
    "Drag and drop PDF invoices here",
    type=['pdf'],
    accept_multiple_files=True,
    help="You can upload multiple PDF files at once."
)

# --- Parsing Button and Logic ---
if st.button("🚀 Parse Invoices", type="primary", disabled=not uploaded_files):
    results = []
    errors = []
    progress_bar = st.progress(0, text="Starting parse...")

    for i, uploaded_file in enumerate(uploaded_files):
        file_content = uploaded_file.getvalue()
        filename = uploaded_file.name
        
        # Call parser function
        result = parse_pdf_invoice(file_content, filename)
        
        if result['status'] == 'success':
            results.append(result['data'])
        else:
            errors.append(result)
        
        progress_bar.progress((i + 1) / len(uploaded_files), text=f"Parsing {filename}...")

    progress_bar.empty()

    if results:
        st.session_state.parsed_data = pd.DataFrame(results)
        st.session_state.edited_data = st.session_state.parsed_data.copy() # Initialize edited data
        st.success(f"Successfully parsed {len(results)} out of {len(uploaded_files)} invoices.")
    else:
        st.session_state.parsed_data = pd.DataFrame()
        st.session_state.edited_data = pd.DataFrame()

    st.session_state.error_log = errors
    if errors:
        st.error(f"Could not parse {len(errors)} file(s). See the error report below.")

# --- Display Parsed Data and Allow Edits ---
if not st.session_state.parsed_data.empty:
    st.header("2. Review and Correct Data")
    st.write("You can edit the values directly in the table below. Changes are saved automatically.")

    # Define column configuration for the data editor
    column_config = {
        "invoice_number": st.column_config.TextColumn("Invoice Number", required=True),
        "invoice_date": st.column_config.TextColumn("Invoice Date", required=True),
        "product_code": st.column_config.SelectboxColumn(
            "Product Code", options=["Leasing", "GEN. EXP", "UNKNOWN"], required=True
        ),
        "net_amount": st.column_config.NumberColumn("Net Amount", format="%.2f", required=True),
        "vat_rate": st.column_config.NumberColumn("VAT Rate", format="%.2f", help="e.g., 0.20 for 20%", required=True),
        "filename": st.column_config.TextColumn("Source File", disabled=True),
    }

    # Use st.data_editor to display and edit data
    edited_df = st.data_editor(
        st.session_state.parsed_data,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="data_editor"
    )

    # Store edits back to session state
    st.session_state.edited_data = edited_df

    # --- Validation Panel ---
    st.subheader("Validation Status")
    
    validation_issues = []
    for index, row in edited_df.iterrows():
        if not row['invoice_number']:
            validation_issues.append(f"Row {index+1}: Missing Invoice Number.")
        if row['product_code'] == 'UNKNOWN':
            validation_issues.append(f"Row {index+1} ({row['filename']}): Unrecognized Product Code.")
        if row['vat_rate'] is None or not (0 < row['vat_rate'] < 1):
             validation_issues.append(f"Row {index+1} ({row['filename']}): Invalid VAT Rate. Should be a decimal (e.g., 0.20).")
    
    if not validation_issues:
        st.success("✅ All rows look good!")
    else:
        st.warning("⚠️ Please fix the following issues:")
        for issue in validation_issues:
            st.write(f"- {issue}")

# --- Error Reporting ---
if st.session_state.error_log:
    st.header("Error Report")
    error_df = pd.DataFrame(st.session_state.error_log)
    st.table(error_df)
    st.download_button(
        label="Download Error Report",
        data=error_df.to_csv(index=False).encode('utf-8'),
        file_name="invoice_parser_error_report.csv",
        mime="text/csv"
    )

# --- Generate Final Upload File ---
if not st.session_state.edited_data.empty:
    st.header("3. Generate and Download Upload File")

    if st.button("Generate Upload File", disabled=(len(validation_issues) > 0)):
        # Build the final DataFrame using the edited data
        upload_ready_df = build_upload_df(st.session_state.edited_data)

        st.subheader("Final Upload Preview")
        st.dataframe(upload_ready_df, use_container_width=True)

        # Generate CSV and JUN file content
        csv_output = upload_ready_df.to_csv(index=False).encode('utf-8')
        
        # Prepare filenames
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = generate_random_suffix()
        jun_filename = f"UPLOAD_{timestamp}_{random_suffix}.JUN"
        csv_filename = "UPLOAD.csv"

        # Display download buttons
        st.subheader("Download Files")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download CSV File",
                data=csv_output,
                file_name=csv_filename,
                mime="text/csv",
            )
        with col2:
            st.download_button(
                label="📥 Download .JUN File",
                data=csv_output, # JUN is the same content, just different name
                file_name=jun_filename,
                mime="application/octet-stream",
            )
