import streamlit as st
from supabase import create_client, Client

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- CUSTOM COLOR STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1 { font-weight: 800 !important; color: #111; letter-spacing: -1.5px; }
    
    /* Status Header Colors */
    .header-potential { color: #E6B800; border-bottom: 2px solid #E6B800; padding-bottom: 5px; font-weight: 700; margin-top: 2rem !important; }
    .header-started { color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 5px; font-weight: 700; margin-top: 2rem !important; }
    .header-trid { color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 5px; font-weight: 700; margin-top: 2rem !important; }
    .header-processing { color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px; font-weight: 700; margin-top: 2rem !important; }
    
    .crm-card {
        background-color: #fff;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; }
    /* Blue link style for DialPad clickability */
    .phone-link { 
        color: #0066ff !important; 
        text-decoration: none !important; 
        font-size: 1rem; 
        font-weight: 600;
        border: 1px solid #eef2ff;
        padding: 4px 8px;
        border-radius: 6px;
        background: #f8faff;
    }
    .phone-link:hover { background: #0066ff; color: white !important; }
    .notes-box { color: #555; font-size: 0.95rem; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; padding-left: 20px; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]
COLOR_MAP = {
    "Potential Lead": "header-potential",
    "Started Application": "header-started",
    "Trid Triggered": "header-trid",
    "In Processing": "header-processing"
}

st.title("Mortgage CRM")

# --- SECTION 1: ADD NEW PROSPECT ---
with st.expander("➕ Create New Record"):
    with st.form("new_lead", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        phone = c2.text_input("Phone")
        stage = c1.selectbox("Status", MY_STATUSES)
        notes = st.text_area("Initial Notes")
        if st.form_submit_button("Confirm Entry"):
            if name and phone:
                supabase.table("prospects").insert({"name": name, "phone": phone, "stage": stage, "notes": notes}).execute()
                st.rerun()

# --- SECTION 2: ONE-CLICK FILTERS ---
st.write("### Filter Pipeline")
filter_cols = st.columns(len(MY_STATUSES) + 1)
if filter_cols[0].button("Show All", use_container_width=True):
    st.session_state.filter = "All"
for i, status in enumerate(MY_STATUSES):
    if filter_cols[i+1].button(status, use_container_width=True):
        st.session_state.filter = status

if 'filter' not in st.session_state:
    st.session_state.filter = "All"

# --- PIPELINE DATA ---
search = st.text_input("", placeholder="🔍 Search by name...")

try:
    data = supabase.table("prospects").select("*").order("name").execute().data
except:
    data = []

if data:
    if search:
        data = [p for p in data if search.lower() in p.get('name','').lower()]

    active_filter = st.session_state.filter
    
    for s in MY_STATUSES:
        if active_filter != "All" and active_filter != s:
            continue
            
        leads = [p for p in data if p.get('stage') == s]
        if leads:
            css_class = COLOR_MAP.get(s, "")
            st.markdown(f'<div class="{css_class}">{s.upper()} ({len(leads)})</div>', unsafe_allow_html=True)
            
            for p in leads:
                p_id = p.get('id')
                # Clean phone number for
