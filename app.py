import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Permanent Mortgage CRM")

# Create a connection to your Google Sheet
# You'll paste your URL in the "Secrets" section of Streamlit (explained below)
conn = st.connection("gsheets", type=GSheetsConnection)

# Read existing data
df = conn.read()

st.title("🏠 Permanent Mortgage CRM")

# --- Form to add data ---
with st.form(key="vendor_form"):
    name = st.text_input("Full Name")
    amount = st.number_input("Loan Amount", step=1000)
    stage = st.selectbox("Stage", ["New Lead", "Prequalified", "In Processing", "Application Submitted"])
    submit_button = st.form_submit_button(label="Save to Google Sheets")

    if submit_button:
        # Create a new row of data
        new_row = pd.DataFrame([{"Name": name, "Loan Amount": amount, "Stage": stage}])
        
        # Add new row to existing data
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Update the Google Sheet
        conn.update(data=updated_df)
        st.success("Data saved successfully!")

st.subheader("Current Leads")
st.dataframe(df)
