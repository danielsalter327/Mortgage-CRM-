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
    .stApp { background-color: #fcfcfc; }
    h1 { font-weight: 800 !important; color: #1a1a1a !important; letter-spacing: -1px; margin-bottom: 0px !important; }
    h4 { margin-top: 2rem !important; color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .status-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
        border-left: 5px solid #1a1a1a;
    }
    .phone-link { color: #007bff !important; text-decoration: none !important; font-weight: 600; font-size: 0.95rem; }
    .notes-text { color: #555; font-size: 0.9rem; line-height: 1.4; font-style: italic; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
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

# --- SECTION 2: PIPELINE (DASHBOARD VIEW) ---
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
            st.markdown(f"#### {s} ({len(stage_leads)})")
            for p in stage_leads:
                p_id = p.get('id')
                p_phone = p.get('phone', '')
                p_notes = p.get('notes', 'No notes added yet.')
                
                with st.container():
                    # The Main Card Layout
                    with st.container():
                        # We use HTML for the card, but Streamlit Columns inside it for the data
                        st.markdown(f'<div class="status-card">', unsafe_allow_html=True)
                        
                        col_info, col_notes, col_actions = st.columns([1, 2, 1])
                        
                        # Col 1: Contact Info
                        with col_info:
                            st.markdown(f"**{p.get('name')}**")
                            st.markdown(f'<a href="tel:{p_phone}" class="phone-link">📞 {p_phone}</a>', unsafe_allow_html=True)
                        
                        # Col 2: The Notes (Utilizing that white space!)
                        with col_notes:
                            st.markdown(f'<div class="notes-text">📝 {p_notes}</div>', unsafe_allow_html=True)
                        
                        # Col 3: Quick Edit/Delete
                        with col_actions:
                            with st.expander("Update"):
                                cur_stage = p.get('stage')
                                s_idx = MY_STATUSES.index(cur_stage) if cur_stage in MY_STATUSES else 0
                                new_stage = st.selectbox("Status", MY_STATUSES, index=s_idx, key=f"s_{p_id}")
                                new_notes = st.text_area("Edit Notes", value=p.get('notes', ''), key=f"n_{p_id}")
                                if st.button("Save", key=f"up_{p_id}"):
                                    supabase.table("prospects").update({"stage": new_stage, "notes": new_notes}).eq("id", p_id).execute()
                                    st.rerun()
                            
                            if st.button("🗑️", key=f"del_{p_id}"):
                                supabase.table("prospects").delete().eq("id", p_id).execute()
                                st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No active prospects.")
