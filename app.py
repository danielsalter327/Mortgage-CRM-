import streamlit as st
from supabase import create_client, Client

# 1. Setup Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Page Tab Title
st.set_page_config(page_title="Mortgage CRM", layout="wide")

# Custom Statuses for your workflow
MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]

# Main Header
st.title("🏠 Mortgage CRM")
st.markdown("---")

# --- SECTION 1: ADD NEW PROSPECT ---
with st.expander("➕ Add New Prospect"):
    with st.form("prospect_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name")
        phone = col2.text_input("Phone Number")
        stage = col1.selectbox("Current Status", MY_STATUSES)
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Save to CRM"):
            if name and phone:
                data = {"name": name, "phone": phone, "stage": stage, "notes": notes}
                try:
                    supabase.table("prospects").insert(data).execute()
                    st.success(f"✅ {name} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please provide Name and Phone Number.")

# --- SECTION 2: VIEW PIPELINE ---
st.subheader("Active Pipeline")

c_search, c_sort = st.columns([2, 1])
search_query = c_search.text_input("🔍 Search by Name", "")
view_mode = c_sort.selectbox("View Mode", ["Group by Status", "All Alphabetical"])

try:
    response = supabase.table("prospects").select("*").order("name").execute()
    prospects = response.data
except Exception as e:
    st.error(f"Database error: {e}")
    prospects = []

if prospects:
    # Filter by search
    if search_query:
        prospects = [p for p in prospects if search_query.lower() in p.get('name', '').lower()]

    if view_mode == "Group by Status":
        for s in MY_STATUSES:
            stage_leads = [p for p in prospects if p.get('stage') == s]
            if stage_leads:
                st.markdown(f"### 📍 {s} ({len(stage_leads)})")
                for p in stage_leads:
                    p_id = p.get('id')
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 2, 1])
                        col1.write(f"👤 **{p.get('name')}**")
                        col2.markdown(f"📞 [Call {p.get('phone')}](tel:{p.get('phone')})")
                        
                        if col3.button("🗑️", key=f"del_{p_id}"):
                            supabase.table("prospects").delete().eq("id", p_id).execute()
                            st.rerun()
                        
                        with st.expander("📝 View Notes / Edit"):
                            current_s = p.get('stage')
                            try:
                                s_index = MY_STATUSES.index(current_s)
                            except ValueError:
                                s_index = 0
                                
                            new_stage = st.selectbox("Update Status", MY_STATUSES, index=s_index, key=f"edit_stage_{p_id}")
                            new_notes = st.text_area("Notes", value=p.get('notes', ''), key=f"edit_notes_{p_id}")
                            
                            if st.button("Save Changes", key=f"save_{p_id}"):
                                supabase.table("prospects").update({"stage": new_stage, "notes": new_notes}).eq("id", p_id).execute()
                                st.rerun()
    else:
        # Simple Alphabetical List
        for p in prospects:
            p_id = p.get('id')
            with st.container(border=True):
                st.write(f"👤 **{p.get('name')}** — {p.get('stage')}")
                st.markdown(f"📞 [Call {p.get('phone')}](tel:{p.get('phone')})")
else:
    st.info("No prospects found.")
