import streamlit as st
import requests
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Mobile Invoice Generator", layout="centered")

st.title("Create Sales Invoice")

# Create the input form
with st.form("invoice_form"):
    st.text_input("Invoice Number", value="Auto-assigned by Tally upon push", disabled=True)
    
    # Updated Company Selection Dropdown
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
    
    # Selection for Local vs Interstate Taxes
    sale_type = st.radio("Sale Type", ["Local (CGST/SGST)", "Interstate (IGST)"])
    
    # Selection for e-Invoice generation
    e_invoice_option = st.radio("Provide e-Invoice Details", ["No (Generate Later)", "Yes (Generate Now)"])
    
    submitted = st.form_submit_button("Push to Database")

if submitted:
    # 1. Format date for Tally (YYYYMMDD)
    formatted_date = date.strftime("%Y%m%d")
    
    # 2. Extract Yes/No for e-Invoice
    e_invoice_val = "Yes" if "Yes" in e_invoice_option else "No"
    
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
                        </ALLLEDGERENTRIES.LIST>
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>2.5% SGST on Sales</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{tax_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>"""
    else:
        tax_amount = base_amount * 0.05  # 5% for IGST
        total_amount = base_amount + tax_amount
        sales_ledger = "5903-5% Interstate-Sales" 
        tax_xml = f"""
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGER
