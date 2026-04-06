import streamlit as st
from supabase import create_client, Client

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- CLEAN AVEN STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1 { font-weight: 800 !important; color: #111; letter-spacing: -1.5px; }
    h4 { margin-top: 2.5rem !important; font-weight: 700; color: #444; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
    
    /* The Unified Card */
    .crm-card {
        background-color: #fff;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 12px;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .crm-card:hover {
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }
    
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; margin-bottom: 4px; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 500; font-size: 0.9rem; }
    .notes-box { color: #666; font-size: 0.95rem; line-height: 1.5; padding: 0 30px; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; }
    
    /* Clean up Streamlit's default padding */
    [data-testid="stVerticalBlock"] > div { padding: 0px !important; }
    .stExpander { border: none !important; box-shadow: none !important; background: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]

st.title("Mortgage CRM")
st.caption("v2.0 | Aven-Style Precision")

# --- ADD NEW PROSPECT ---
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

# --- PIPELINE ---
search = st.text_input("", placeholder="🔍 Search by name...")

try:
    data = supabase.table("prospects").select("*").order("name").execute().data
except:
    data = []

if data:
    if search:
        data = [p for p in data if search.lower() in p.get('name','
