import streamlit as st
import requests
from datetime import datetime

# Configure page for mobile screens
st.set_page_config(page_title="Mobile Invoice Generator", layout="centered")

st.title("Create Sales Invoice")

# Create the input form
with st.form("invoice_form"):
    date = st.date_input("Invoice Date", datetime.today())
    party_name = st.text_input("Customer Ledger Name (Exact match)")
    item_name = st.text_input("Stock Item Name (Exact match)")
    quantity = st.number_input("Quantity", min_value=1, value=1)
    rate = st.number_input("Rate per unit", min_value=0.0, format="%.2f")
    
    submit_button = st.form_submit_button("Push to Database")

if submit_button:
    amount = quantity * rate
    tally_date = date.strftime("%Y%m%d")
    
    # XML Payload configured for Sales Voucher creation
    xml_data = f"""<ENVELOPE>
      <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
      </HEADER>
      <BODY>
        <IMPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>Vouchers</REPORTNAME>
          </REQUESTDESC>
          <REQUESTDATA>
            <TALLYMESSAGE xmlns:UDF="TallyUDF">
              <VOUCHER VCHTYPE="Sales" ACTION="Create">
                <DATE>{tally_date}</DATE>
                <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
                
                <!-- Party Ledger Entry -->
                <ALLLEDGERENTRIES.LIST>
                  <LEDGERNAME>{party_name}</LEDGERNAME>
                  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                  <AMOUNT>-{amount}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
                
                <!-- Sales Account Ledger Entry -->
                <ALLLEDGERENTRIES.LIST>
                  <LEDGERNAME>Sales Account</LEDGERNAME>
                  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                  <AMOUNT>{amount}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
                
                <!-- Inventory Entry -->
                <ALLINVENTORYENTRIES.LIST>
                  <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
                  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                  <BILLEDQTY>{quantity} NOS</BILLEDQTY>
                  <RATE>{rate}/NOS</RATE>
                  <AMOUNT>{amount}</AMOUNT>
                </ALLINVENTORYENTRIES.LIST>
              </VOUCHER>
            </TALLYMESSAGE>
          </REQUESTDATA>
        </IMPORTDATA>
      </BODY>
    </ENVELOPE>"""

    # Replace with your active Ngrok URL routing to port 9000
    url = "https://consensus-geology-cobalt.ngrok-free.dev" 
    headers = {'Content-Type': 'text/xml'}

    try:
        response = requests.post(url, data=xml_data, headers=headers)
        
        # Check if the voucher was successfully created
        if "<CREATED>1</CREATED>" in response.text:
            st.success("Invoice successfully created!")
        else:
            st.error(f"Database Error: {response.text}")
    except Exception as e:
        st.error(f"Connection failed: {e}. Check your Ngrok tunnel.")
