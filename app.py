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
        align-items: center;
    }
    .crm-card:hover {
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }
    
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; margin-bottom: 4px; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 500; font-size: 0.9rem; }
    .notes-box { color: #555; font-size: 0.95rem; line-height: 1.5; padding: 0 30px; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; }
    
    /* Formatting Action Row */
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; border: 1px solid #eee; }
    .stExpander { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]

st.title("Mortgage CRM")
st.caption("Secure Pipeline Management • Fintech Edition")

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
    # FIXED LINE 72 HERE
    if search:
        data = [p for p in data if search.lower() in p.get('name','').lower()]

    for s in MY_STATUSES:
        leads = [p for p in data if p.get('stage') == s]
        if leads:
            st.markdown(f"#### {s} • {len(leads)}")
            for p in leads:
                p_id = p.get('id')
                with st.container():
                    st.markdown(f"""
                        <div class="crm-card">
                            <div style="min-width: 180px;">
                                <div class="name-text">{p.get('name')}</div>
                                <a href="tel:{p.get('phone')}" class="phone-link">📞 {p.get('phone')}</a>
                            </div>
                            <div class="notes-box">
                                {p.get('notes') if p.get('notes') else '<span style="color:#ccc">No notes recorded.</span>'}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    edit_col, del_col, spacer = st.columns([1, 1, 6])
                    with edit_col.expander("Edit"):
                        new_s = st.selectbox("Status", MY_STATUSES, index=MY_STATUSES.index(p.get('stage')), key=f"s_{p_id}")
                        new_n = st.text_area("Notes", value=p.get('notes',''), key=f"n_{p_id}")
                        if st.button("Save Changes", key=f"up_{p_id}"):
                            supabase.table("prospects").update({"stage": new_s, "notes": new_n}).eq("id", p_id).execute()
                            st.rerun()
                    if del_col.button("🗑️", key=f"del_{p_id}"):
                        supabase.table("prospects").delete().eq("id", p_id).execute()
                        st.rerun()
else:
    st.info("Pipeline is empty.")
