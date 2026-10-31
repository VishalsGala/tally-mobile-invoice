import streamlit as st
import requests
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Mobile Invoice Generator", layout="centered")

st.title("Create Sales Invoice")

# Create the input form
with st.form("invoice_form"):
    # Display a placeholder letting the user know Tally handles the numbering
    st.text_input("Invoice Number", value="Auto-assigned by Tally upon push", disabled=True)
    
    date = st.date_input("Invoice Date", datetime.today())
    party_name = st.text_input("Customer Name (Exact Tally Ledger Name)")
    item_name = st.text_input("Stock Item Name")
    quantity = st.number_input("Quantity (in Mtr)", min_value=1.0, value=1.0, step=1.0)
    rate = st.number_input("Rate per unit", min_value=0.01, value=145.00, step=0.01)
    
    # Selection for Local vs Interstate Taxes
    sale_type = st.radio("Sale Type", ["Local (CGST/SGST)", "Interstate (IGST)"])
    
    submitted = st.form_submit_button("Push to Database")

if submitted:
    # 1. Format date for Tally (YYYYMMDD)
    formatted_date = date.strftime("%Y%m%d")
    
    # 2. Calculate Amounts and Tax XML based on selection
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
                            <LEDGERNAME>5% IGST on Sales</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{tax_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>"""

    # 3. Build the XML Payload (VOUCHERNUMBER tag removed so Tally auto-generates it)
    xml_data = f"""<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>ANKIT ENTERPRISE</SVCURRENTCOMPANY>
                </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Accounting Voucher View">
                        <DATE>{formatted_date}</DATE>
                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                        <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
                        
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{party_name}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{total_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{sales_ledger}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{base_amount}</AMOUNT>
                            <INVENTORYALLOCATIONS.LIST>
                                <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
                                <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                <BILLEDQTY>{quantity} Mtr</BILLEDQTY>
                                <RATE>{rate}/Mtr</RATE>
                                <AMOUNT>{base_amount}</AMOUNT>
                            </INVENTORYALLOCATIONS.LIST>
                        </ALLLEDGERENTRIES.LIST>
                        {tax_xml}
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>"""

    # 4. Push to Tally via Ngrok Tunnel
    url = "https://consensus-geology-cobalt.ngrok-free.dev"
    headers = {'Content-Type': 'text/xml'}
    
    try:
        response = requests.post(url, data=xml_data.encode('utf-8'), headers=headers)
        
        # 5. Check Response from Tally
        if "<CREATED>1</CREATED>" in response.text:
            st.success("Invoice successfully created! Tally has automatically assigned the next invoice number.")
        else:
            st.error(f"Database Error: {response.text}")
    except Exception as e:
        st.error(f"Connection failed: {e}. Check if your Ngrok tunnel is running on the desktop.")
