import streamlit as st
from supabase import create_client, Client

# 1. Setup Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage Vault CRM", layout="wide")

st.title("🏦 Mortgage Vault CRM")

# --- ADD PROSPECT ---
with st.expander("➕ Add New Prospect"):
    with st.form("prospect_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        amount = st.number_input("Loan Amount", step=1000)
        stage = st.selectbox("Stage", ["New Lead", "Prequalified", "In Processing", "Application"])
        
        if st.form_submit_button("Securely Save"):
            data = {"name": name, "phone": phone, "amount": amount, "stage": stage}
            supabase.table("prospects").insert(data).execute()
            st.success(f"Saved {name} to the Vault!")
            st.rerun()

# --- VIEW PIPELINE ---
st.subheader("Your Active Pipeline")
response = supabase.table("prospects").select("*").execute()
prospects = response.data

if prospects:
    for p in prospects:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.write(f"**{p['name']}**")
            col2.markdown(f"📞 [Call {p['phone']}](tel:{p['phone']})")
            col3.write(f"${p['amount']:,}")
else:
    st.info("No prospects in the vault yet.")
