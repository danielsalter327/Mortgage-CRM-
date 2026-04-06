import streamlit as st
from supabase import create_client, Client

# 1. Setup Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- AVEN-INSPIRED STYLING ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfcfc;
    }
    h1 {
        font-weight: 800 !important;
        color: #1a1a1a !important;
        letter-spacing: -1px;
        margin-bottom: 0px !important;
    }
    .status-card {
        background-color: white;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
        border-left: 5px solid #1a1a1a;
    }
    .phone-link {
        color: #007bff !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .phone-link:hover {
        text-decoration: underline !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]

st.title("Mortgage CRM")
st.caption("Secure Pipeline Management")

# --- SECTION 1: ADD NEW PROSPECT ---
with st.expander("➕ Add New Prospect"):
    with st.form("prospect_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name")
        phone = col2.text_input("Phone Number")
        stage = col1.selectbox("Current Status", MY_STATUSES)
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Add to Pipeline"):
            if name and phone:
                data = {"name": name, "phone": phone, "stage": stage, "notes": notes}
                try:
                    supabase.table("prospects").insert(data).execute()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- SECTION 2: PIPELINE ---
search_query = st.text_input("", placeholder="🔍 Search prospects...")

try:
    response = supabase.table("prospects").select("*").order("name").execute()
    prospects = response.data
except:
    prospects = []

if prospects:
    if search_query:
        prospects = [p for p in prospects if search_query.lower() in p.get('name', '').lower()]

    for s in MY_STATUSES:
        stage_leads = [p for p in prospects if p.get('stage') == s]
        if stage_leads:
            st.markdown(f"#### {s}")
            for p in stage_leads:
                p_id = p.get('id')
                p_phone = p.get('phone', '')
                
                with st.container():
                    # THE CLICK-TO-CALL CARD
                    st.markdown(f"""
                    <div class="status-card">
                        <div style="font-size: 1.05rem; font-weight: 700;">{p.get('name')}</div>
                        <a href="tel:{p_phone}" class="phone-link">📞 {p_phone}</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_edit, col_del = st.columns([5, 1])
                    with col_edit.expander("View details & edit"):
                        cur_stage = p.get('stage')
                        s_idx = MY_STATUSES.index(cur_stage) if cur_stage in MY_STATUSES else 0
                        new_stage = st.selectbox("Status", MY_STATUSES, index=s_idx, key=f"s_{p_id}")
                        new_notes = st.text_area("Notes", value=p.get('notes', ''), key=f"n_{p_id}")
                        if st.button("Update", key=f"up_{p_id}"):
                            supabase.table("prospects").update({"stage": new_stage, "notes": new_notes}).eq("id", p_id).execute()
                            st.rerun()
                    
                    if col_del.button("🗑️", key=f"del_{p_id}"):
                        supabase.table("prospects").delete().eq("id", p_id).execute()
                        st.rerun()
else:
    st.info("No active prospects.")
