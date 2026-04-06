import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Mortgage Pro CRM", layout="wide")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch data (clearing cache so it's always fresh)
df = conn.read(ttl=0)

st.title("🏠 Mortgage Prospect Manager")

# --- ACTION TABS ---
tab1, tab2 = st.tabs(["➕ Add New Prospect", "📋 View & Call Pipeline"])

with tab1:
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name")
        phone = col2.text_input("Phone Number (e.g. 555-123-4567)")
        amount = col1.number_input("Loan Amount", min_value=0, step=5000)
        stage = col2.selectbox("Stage", ["New Lead", "Prequalified", "In Processing", "Application Submitted"])
        
        if st.form_submit_button("Save Prospect"):
            if name and phone:
                new_data = pd.DataFrame([{"Name": name, "Phone": phone, "Loan Amount": amount, "Stage": stage}])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"Added {name} to the database!")
                st.rerun()
            else:
                st.error("Please provide at least a Name and Phone Number.")

with tab2:
    # Search Filter
    search = st.text_input("🔍 Search by Name", "")
    
    # Filter the dataframe
    if search:
        display_df = df[df['Name'].str.contains(search, case=False, na=False)]
    else:
        display_df = df

    # Display Leads with "Click-to-Call" links
    for index, row in display_df.iterrows():
        with st.expander(f"{row['Name']} — {row['Stage']}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**Loan:** ${row['Loan Amount']:,}")
            
            # This creates a link that opens the phone dialer
            phone_url = f"tel:{row['Phone']}"
            c2.markdown(f"📞 [Call {row['Phone']}]({phone_url})")
            
            if c3.button("Delete", key=f"del_{index}"):
                df = df.drop(index)
                conn.update(data=df)
                st.rerun()
