import streamlit as st
from supabase import create_client, Client

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .header-potential { color: #E6B800; border-bottom: 2px solid #E6B800; font-weight: 700; margin-top: 2rem !important; }
    .header-started { color: #28a745; border-bottom: 2px solid #28a745; font-weight: 700; margin-top: 2rem !important; }
    .header-trid { color: #dc3545; border-bottom: 2px solid #dc3545; font-weight: 700; margin-top: 2rem !important; }
    .header-processing { color: #007bff; border-bottom: 2px solid #007bff; font-weight: 700; margin-top: 2rem !important; }
    
    .task-card { background: #fff5f5; border: 1px solid #ffe3e3; padding: 10px; border-radius: 8px; margin-bottom: 5px; display: flex; justify-content: space-between; }
    .crm-card { background-color: #fff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 600; }
    .notes-box { color: #555; font-size: 0.95rem; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; padding-left: 20px; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]
COLOR_MAP = {"Potential Lead": "header-potential", "Started Application": "header-started", "Trid Triggered": "header-trid", "In Processing": "header-processing"}

st.title("Mortgage CRM")

# --- SECTION: GLOBAL TASKS ---
st.subheader("📋 Pending Tasks")
try:
    # Get all incomplete tasks and join with prospect names
    task_resp = supabase.table("tasks").select("*, prospects(name)").eq("is_completed", False).execute()
    tasks = task_resp.data
    if tasks:
        for t in tasks:
            col_t, col_b = st.columns([5, 1])
            p_name = t.get('prospects', {}).get('name', 'General')
            col_t.markdown(f"🔔 **{p_name}**: {t['task_text']}")
            if col_b.button("Done", key=f"done_{t['id']}"):
                supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                st.rerun()
    else:
        st.caption("No pending tasks. You're all caught up!")
except Exception as e:
    st.error(f"Task Error: {e}")

st.markdown("---")

# --- ADD NEW PROSPECT ---
with st.expander("➕ Create New Record"):
    with st.form("new_lead"):
        c1, c2 = st.columns(2)
        name, phone = c1.text_input("Name"), c2.text_input("Phone")
        stage, notes = c1.selectbox("Status", MY_STATUSES), st.text_area("Initial Notes")
        if st.form_submit_button("Confirm"):
            supabase.table("prospects").insert({"name": name, "phone": phone, "stage": stage, "notes": notes}).execute()
            st.rerun()

# --- PIPELINE ---
search = st.text_input("", placeholder="🔍 Search by name...")
if 'filter' not in st.session_state: st.session_state.filter = "All"
f_cols = st.columns(len(MY_STATUSES) + 1)
if f_cols[0].button("Show All"): st.session_state.filter = "All"
for i, s in enumerate(MY_STATUSES):
    if f_cols[i+1].button(s): st.session_state.filter = s

try:
    data = supabase.table("prospects").select("*").order("name").execute().data
    if search: data = [p for p in data if search.
