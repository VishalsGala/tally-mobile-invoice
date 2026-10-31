import streamlit as st
import requests
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Mobile Invoice Generator", layout="centered")

st.title("Create Sales Invoice")

# Create the input form
with st.form("invoice_form"):
    st.text_input("Invoice Number", value="Auto-assigned by Tally upon push", disabled=True)
    
    # Company Selection
    company_name = st.selectbox("Select Company", [
        "Ankit Enterprise", 
        "Shree Ashapura Trading Company", 
        "Laxmi Impex", 
        "Ankit Enterprise (Partnership firm)"
    ])
    
    date = st.date_input("Invoice Date", datetime.today())
    party_name = st.text_input("Customer Name (Exact Tally Ledger Name)")
    item_name = st.text_input("Stock Item Name")
    quantity = st.number_input("Quantity (in Mtr)", min_value=1.0, value=1.0, step=1.0)
    rate = st.number_input("Rate per unit", min_value=0.01, value=145.00, step=0.01)
    
    # Taxes and E-Invoice Options
    sale_type = st.radio("Sale Type", ["Local (CGST/SGST)", "Interstate (IGST)"])
    e_invoice_option = st.radio("Provide e-Invoice Details", ["No", "Yes"])
    
    # Manual E-Way Bill Inputs
    e_way_bill_option = st.radio("Provide e-Way Bill Details", ["No", "Yes (Enter Manually)"])
    eway_bill_no = st.text_input("E-Way Bill No. (Leave blank if No)")
    eway_bill_date = st.date_input("E-Way Bill Date (Applies only if Yes)", datetime.today())
    
    submitted = st.form_submit_button("Push to Database")

if submitted:
    # 1. Format dates for Tally (YYYYMMDD)
    formatted_date = date.strftime("%Y%m%d")
    fmt_eway_date = eway_bill_date.strftime("%Y%m%d")
    
    # 2. Extract Yes/No selections
    e_invoice_val = "Yes" if "Yes" in e_invoice_option else "No"
    e_way_bill_val = "Yes" if "Yes" in e_way_bill_option else "No"
    
    # 3. Calculate Amounts and Tax XML based on selection
    base_amount = quantity * rate
    
    if sale_type == "Local (CGST/SGST)":
        tax_amount = base_amount * 0.025  # 2.5% for CGST/SGST
        total_amount = base_amount + (tax_amount * 2)
        sales_ledger = "5903-5% Local-Sales"
        tax_xml = f"""
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>2.5% CGST on Sales</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{tax_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST
