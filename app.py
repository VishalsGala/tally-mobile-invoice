import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Mobile Invoice Generator", layout="centered")

# --- SECURITY LOCK ---
# Change "12345" to your desired secret PIN or password
APP_PASSWORD = "Nchheda@985"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 App Locked")
    pwd = st.text_input("Enter Access PIN", type="password")
    if st.button("Unlock"):
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Access Denied: Incorrect PIN")
    st.stop()  # Prevents the rest of the app from loading until unlocked
# ---------------------

st.title("Create Sales Invoice")

url = "https://consensus-geology-cobalt.ngrok-free.dev"

# Helper function to fetch live customers from Tally
def get_tally_customers(company):
    req_xml = f"""<ENVELOPE>
        <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Accounts</REPORTNAME>
                    <STATICVARIABLES>
                        <SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>
                        <GROUPNAME>Sundry Debtors</GROUPNAME>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>"""
    try:
        res = requests.post(url, data=req_xml.encode('utf-8'), headers={'Content-Type': 'text/xml'}, timeout=5)
        if res.status_code == 200 and "ERR_NGROK" not in res.text:
            root = ET.fromstring(res.text)
            names = [elem.text for elem in root.findall('.//NAME') if elem.text]
            return sorted(list(set(names)))
    except Exception:
        pass
    return []

# Helper function to fetch live stock items from Tally
def get_tally_items(company):
    req_xml = f"""<ENVELOPE>
        <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Accounts</REPORTNAME>
                    <STATICVARIABLES>
                        <SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>
                        <ACCOUNTTYPE>Stock Items</ACCOUNTTYPE>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>"""
    try:
        res = requests.post(url, data=req_xml.encode('utf-8'), headers={'Content-Type': 'text/xml'}, timeout=5)
        if res.status_code == 200 and "ERR_NGROK" not in res.text:
            root = ET.fromstring(res.text)
            names = [elem.text for elem in root.findall('.//NAME') if elem.text]
            return sorted(list(set(names)))
    except Exception:
        pass
    return []

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
    
    # Dynamic Customer Fetching
    live_customers = get_tally_customers(company_name)
    if live_customers:
        party_name = st.selectbox("Customer Name", live_customers)
    else:
        party_name = st.text_input("Customer Name (Exact Tally Ledger Name) - Tunnel Offline")
        
    # Dynamic Stock Item Fetching
    live_items = get_tally_items(company_name)
    if live_items:
        item_name = st.selectbox("Stock Item Name", live_items)
    else:
        item_name = st.text_input("Stock Item Name (Exact Tally Name) - Tunnel Offline")
        
    quantity = st.number_input("Quantity (in Mtr)", min_value=1.0, value=1.0, step=1.0)
    rate = st.number_input("Rate per unit", min_value=0.01, value=145.00, step=0.01)
    
    # Taxes and E-Invoice Options
    sale_type = st.radio("Sale Type", ["Local (CGST/SGST)", "Interstate (IGST)"])
    e_invoice_option = st.radio("Generate E-invoice", ["No", "Yes"])
    
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
        tax_xml = f"""<ALLLEDGERENTRIES.LIST>
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
        tax_xml = f"""<ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>5% IGST on Sales</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{tax_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>"""

    # Build E-Way Bill XML block if enabled and a number is provided
    eway_xml = ""
    if e_way_bill_val == "Yes" and eway_bill_no.strip():
        eway_xml = f"""<EWAYBILLDETAILS.LIST>
                            <EWAYBILLNO>{eway_bill_no.strip()}</EWAYBILLNO>
                            <EWAYBILLDATE>{fmt_eway_date}</EWAYBILLDATE>
                        </EWAYBILLDETAILS.LIST>"""

    # 4. Build the XML Payload 
    xml_data = f"""<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Accounting Voucher View">
                        <DATE>{formatted_date}</DATE>
                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                        <PROVIDEEINVOICEDETAILS>{e_invoice_val}</PROVIDEEINVOICEDETAILS>
                        <PROVIDEEWAYBILLDETAILS>{e_way_bill_val}</PROVIDEEWAYBILLDETAILS>
                        <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
                        {eway_xml}
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
    
    try:
        response = requests.post(url, data=xml_data.encode('utf-8'), headers={'Content-Type': 'text/xml'})
        
        # 5. Check Response from Tally or Ngrok
        if "ERR_NGROK" in response.text:
            st.error("Ngrok tunnel is offline. Please restart 'ngrok http 9000' on your desktop and try again.")
        elif "<CREATED>1</CREATED>" in response.text:
            st.success(f"Invoice successfully created in {company_name}! Tally has automatically assigned the next invoice number.")
        else:
            st.error(f"Database Error: {response.text}")
    except Exception as e:
        st.error(f"Connection failed: {e}. Check if your Ngrok tunnel is running on the desktop.")
        
