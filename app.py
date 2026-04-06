import streamlit as st
from supabase import create_client, Client

# 1. Setup Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage Vault CRM", layout="wide")

st.title("🏠 Mortgage Vault CRM")
st.markdown("---")

# --- SECTION 1: ADD NEW PROSPECT ---
with st.expander("➕ Add New Prospect"):
    with st.form("prospect_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name")
        phone = col2.text_input("Phone Number")
        stage = col1.selectbox("Current Stage", ["New Lead", "Prequalified", "In Processing", "Application"])
        notes = st.text_area("Notes (Special requirements or follow-up info)")
        
        if st.form_submit_button("Securely Save to Vault"):
            if name and phone:
                # REMOVED 'amount' FROM THIS DICTIONARY
                data = {
                    "name": name, 
                    "phone": phone, 
                    "stage": stage, 
                    "notes": notes
                }
                try:
                    supabase.table("prospects").insert(data).execute()
                    st.success(f"✅ Saved {name} to the Vault!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving: {e}")
            else:
                st.warning("Please provide at least a Name and Phone Number.")

# --- SECTION 2: VIEW PIPELINE ---
st.subheader("Your Active Pipeline")
search_query = st.text_input("🔍 Search by Name", "")

try:
    response = supabase.table("prospects").select("*").order("name").execute()
    prospects = response.data
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    prospects = []

if prospects:
    if search_query:
        prospects = [p for p in prospects if search_query.lower() in p.get('name', '').lower()]

    for p in prospects:
        p_id = p.get('id')
        p_name = p.get('name', 'Unknown')
        p_phone = p.get('phone', '')
        p_stage = p.get('stage', 'New Lead')
        p_notes = p.get('notes', '')

        with st.container(border=True):
            # Adjusted columns since we have one less piece of data
            c1, c2, c3 = st.columns([3, 2, 1])
            
            c1.write(f"👤 **{p_name}**")
            c1.caption(f"Status: {p_stage}")
            
            if p_phone:
                c2.markdown(f"📞 [Call {p_phone}](tel:{p_phone})")
            
            if p_id:
                if c3.button("🗑️ Delete", key=f"del_{p_id}"):
                    supabase.table("prospects").delete().eq("id", p_id).execute()
                    st.rerun()
            
            if p_notes:
                st.info(f"📝 **Notes:** {p_notes}")
else:
    st.info("No prospects found.")
