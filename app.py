import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Mobile Invoice Generator", layout="centered")

# --- SECURITY LOCK ---
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
    st.stop()
# ---------------------

st.title("Create Sales Invoice")

url = "https://consensus-geology-cobalt.ngrok-free.dev"

# Required header to bypass Ngrok's free-tier HTML warning page
api_headers = {
    'Content-Type': 'text/xml',
    'ngrok-skip-browser-warning': 'true'
}

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
        res = requests.post(url, data=req_xml.encode('utf-8'), headers=api_headers, timeout=5)
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
        res = requests.post(url, data=req_xml.encode('utf-8'), headers=api_headers, timeout=5)
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
    # 1. Format
