import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Tally Mobile ERP", layout="centered", initial_sidebar_state="expanded")

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

url = "https://consensus-geology-cobalt.ngrok-free.dev"

# Upgraded headers to mask the request and bypass Ngrok warnings
api_headers = {
    'Content-Type': 'text/xml', 
    'ngrok-skip-browser-warning': 'any',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': '*/*'
}

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Sales Invoice", "Receipt Entry"])

# Shared Helper Functions
def get_tally_customers(company):
    req_xml = f"""<ENVELOPE><HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER><BODY><EXPORTDATA><REQUESTDESC><REPORTNAME>List of Accounts</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY><GROUPNAME>Sundry Debtors</GROUPNAME></STATICVARIABLES></REQUESTDESC></EXPORTDATA></BODY></ENVELOPE>"""
    try:
        res = requests.post(url, data=req_xml.encode('utf-8'), headers=api_headers, timeout=15)
        if res.status_code == 200 and "ERR_NGROK" not in res.text and "<html" not in res.text.lower():
            root = ET.fromstring(res.text)
            names = [elem.text for elem in root.findall('.//NAME') if elem.text]
            if names:
                return sorted(list(set(names)))
    except Exception:
        pass
    return []

def get_tally_items(company):
    req_xml = f"""<ENVELOPE><HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER><BODY><EXPORTDATA><REQUESTDESC><REPORTNAME>List of Accounts</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY><ACCOUNTTYPE>Stock Items</ACCOUNTTYPE></STATICVARIABLES></REQUESTDESC></EXPORTDATA></BODY></ENVELOPE>"""
    try:
        res = requests.post(url, data=req_xml.encode('utf-8'), headers=api_headers, timeout=15)
        if res.status_code == 200 and "ERR_NGROK" not in res.text and "<html" not in res.text.lower():
            root = ET.fromstring(res.text)
            names = [elem.text for elem in root.findall('.//NAME') if elem.text]
            if names:
                return sorted(list(set(names)))
    except Exception:
        pass
    return []

# Shared Company Selection
companies = ["Ankit Enterprise", "Shree Ashapura Trading Company", "Laxmi Impex", "Ankit Enterprise (Partnership firm)"]

# ==========================================
# MODULE 1: SALES INVOICE
# ==========================================
if menu == "Sales Invoice":
    st.title("Create Sales Invoice")
    
    with st.form("invoice_form"):
        st.text_input("Invoice Number", value="Auto-assigned by Tally upon push", disabled=True)
        company_name = st.selectbox("Select Company", companies, key="sales_company")
        date = st.date_input("Invoice Date", datetime.today(), key="sales_date")
        
        live_customers = get_tally_customers(company_name)
        party_name = st.selectbox("Customer Name", live_customers) if live_customers else st.text_input("Customer Name - Tunnel Offline or Tally Timeout")
            
        live_items = get_tally_items(company_name)
        item_name = st.selectbox("Stock Item Name", live_items) if live_items else st.text_input("Stock Item Name - Tunnel Offline or Tally Timeout")
            
        quantity = st.number_input("Quantity (in Mtr)", min_value=1.0, value=1.0, step=1.0)
        rate = st.number_input("Rate per unit", min_value=0.01, value=145.00, step=0.01)
        
        sale_type = st.radio("Sale Type", ["Local (CGST/SGST)", "Interstate (IGST)"])
        e_invoice_option = st.radio("Generate E-invoice", ["No", "Yes"])
        e_way_bill_option = st.radio("Provide e-Way Bill Details", ["No", "Yes (Enter Manually)"])
        eway_bill_no = st.text_input("E-Way Bill No. (Leave blank if No)")
        eway_bill_date = st.date_input("E-Way Bill Date (Applies only if Yes)", datetime.today())
        
        if st.form_submit_button("Push Sales Invoice"):
            formatted_date = date.strftime("%Y%m%d")
            fmt_eway_date = eway_bill_date.strftime("%Y%m%d")
            e_invoice_val = "Yes" if "Yes" in e_invoice_option else "No"
            e_way_bill_val = "Yes" if "Yes" in e_way_bill_option else "No"
            
            base_amount = quantity * rate
            
            if sale_type == "Local (CGST/SGST)":
                tax_amount = base_amount * 0.025
                total_amount = base_amount + (tax_amount * 2)
                sales_ledger = "5903-5% Local-Sales"
                tax_xml = f"""<ALLLEDGERENTRIES.LIST><LEDGERNAME>2.5% CGST on Sales</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{tax_amount}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>2.5% SGST on Sales</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{tax_amount}</AMOUNT></ALLLEDGERENTRIES.LIST>"""
            else:
                tax_amount = base_amount * 0.05
                total_amount = base_amount + tax_amount
                sales_ledger = "OMS 5% GST" 
                tax_xml = f"""<ALLLEDGERENTRIES.LIST><LEDGERNAME>OMS 5% GST</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{tax_amount}</AMOUNT></ALLLEDGERENTRIES.LIST>"""

            eway_xml = f"""<EWAYBILLDETAILS.LIST><EWAYBILLNO>{eway_bill_no.strip()}</EWAYBILLNO><EWAYBILLDATE>{fmt_eway_date}</EWAYBILLDATE></EWAYBILLDETAILS.LIST>""" if e_way_bill_val == "Yes" and eway_bill_no.strip() else ""

            xml_data = f"""<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC><REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Accounting Voucher View"><DATE>{formatted_date}</DATE><VOUCHERTYPENAME>Sales</VOUCHERTYPENAME><PROVIDEEINVOICEDETAILS>{e_invoice_val}</PROVIDEEINVOICEDETAILS><PROVIDEEWAYBILLDETAILS>{e_way_bill_val}</PROVIDEEWAYBILLDETAILS><PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>{eway_xml}<ALLLEDGERENTRIES.LIST><LEDGERNAME>{party_name}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{total_amount}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{sales_ledger}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{base_amount}</AMOUNT><INVENTORYALLOCATIONS.LIST><STOCKITEMNAME>{item_name}</STOCKITEMNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><BILLEDQTY>{quantity} Mtr</BILLEDQTY><RATE>{rate}/Mtr</RATE><AMOUNT>{base_amount}</AMOUNT></INVENTORYALLOCATIONS.LIST></ALLLEDGERENTRIES.LIST>{tax_xml}</VOUCHER></TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
            
            try:
                response = requests.post(url, data=xml_data.encode('utf-8'), headers=api_headers, timeout=15)
                if "ERR_NGROK" in response.text:
                    st.error("Ngrok tunnel offline.")
                elif "<CREATED>1</CREATED>" in response.text:
                    st.success("Sales Invoice created successfully!")
                else:
                    st.error(f"Database Error: {response.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# ==========================================
# MODULE 2: RECEIPT ENTRY
# ==========================================
elif menu == "Receipt Entry":
    st.title("Enter Payment Receipt")
    
    with st.form("receipt_form"):
        company_name = st.selectbox("Select Company", companies, key="receipt_company")
        date = st.date_input("Receipt Date", datetime.today(), key="receipt_date")
        
        live_customers = get_tally_customers(company_name)
        party_name = st.selectbox("Received From", live_customers) if live_customers else st.text_input("Customer Name - Tunnel Offline or Tally Timeout")
        
        receipt_mode = st.selectbox("Payment Mode", ["Cash", "Bank Account (NEFT/RTGS/UPI)"])
        amount = st.number_input("Amount Received", min_value=1.0, value=1000.0, step=1.0)
        narration = st.text_input("Narration (Optional)")
        
        if st.form_submit_button("Push Receipt"):
            formatted_date = date.strftime("%Y%m%d")
            ledger_account = "Cash" if receipt_mode == "Cash" else "Bank" # Ensure "Bank" ledger matches exact Tally name
            
            xml_data = f"""<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC><REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Receipt" ACTION="Create"><DATE>{formatted_date}</DATE><VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME><NARRATION>{narration}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{party_name}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{amount}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{ledger_account}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{amount}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
            
            try:
                response = requests.post(url, data=xml_data.encode('utf-8'), headers=api_headers, timeout=15)
                if "ERR_NGROK" in response.text:
                    st.error("Ngrok tunnel offline.")
                elif "<CREATED>1</CREATED>" in response.text:
                    st.success("Receipt Voucher created successfully!")
                else:
                    st.error(f"Database Error: {response.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# END OF SCRIPT
