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
        stage = col1.selectbox("Current Stage", ["New Lead", "Prequalified", "In Processing", "Application"], key="new_stage")
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Securely Save to Vault"):
            if name and phone:
                data = {"name": name, "phone": phone, "stage": stage, "notes": notes}
                try:
                    supabase.table("prospects").insert(data).execute()
                    st.success(f"✅ Saved {name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Name and Phone required.")

# --- SECTION 2: VIEW & EDIT PIPELINE ---
st.subheader("Your Active Pipeline")
search_query = st.text_input("🔍 Search by Name", "")

try:
    response = supabase.table("prospects").select("*").order("name").execute()
    prospects = response.data
except Exception as e:
    st.error(f"Database error: {e}")
    prospects = []

if prospects:
    if search_query:
        prospects = [p for p in prospects if search_query.lower() in p.get('name', '').lower()]

    for p in prospects:
        p_id = p.get('id')
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            
            c1.write(f"👤 **{p.get('name')}**")
            c1.caption(f"Current Status: {p.get('stage')}")
            c2.markdown(f"📞 [Call {p.get('phone')}](tel:{p.get('phone')})")
            
            # Delete Button
            if p_id and c3.button("🗑️", key=f"del_{p_id}"):
                supabase.table("prospects").delete().eq("id", p_id).execute()
                st.rerun()
            
            # --- EDIT SECTION ---
            with st.expander("📝 Edit Notes & Status"):
                # Pre-fill with current data
                new_stage = st.selectbox("Update Stage", 
                                         ["New Lead", "Prequalified", "In Processing", "Application"], 
                                         index=["New Lead", "Prequalified", "In Processing", "Application"].index(p.get('stage', 'New Lead')),
                                         key=f"stage_{p_id}")
                
                new_notes = st.text_area("Edit Notes", value=p.get('notes', ''), key=f"notes_{p_id}")
                
                if st.button("Save Changes", key=f"save_{p_id}"):
                    update_data = {"stage": new_stage, "notes": new_notes}
                    supabase.table("prospects").update(update_data).eq("id", p_id).execute()
                    st.success("Updated!")
                    st.rerun()
            
            if p.get('notes') and not search_query: # Hide preview notes if searching to keep it clean
                st.caption(f"**Quick View Notes:** {p['notes']}")
else:
    st.info("No prospects found.")
