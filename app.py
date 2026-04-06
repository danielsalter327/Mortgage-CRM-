import streamlit as st
from supabase import create_client, Client

# 1. Setup Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- AVEN-INSPIRED STYLING (Custom CSS) ---
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #fcfcfc;
    }
    
    /* Title styling */
    h1 {
        font-weight: 800 !important;
        color: #1a1a1a !important;
        letter-spacing: -1px;
    }
    
    /* Card Styling */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stExpander"]) {
        border: none !important;
    }
    
    .status-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        border-left: 5px solid #1a1a1a;
    }
    
    /* Button Styling */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background-color: white;
        color: #1a1a1a;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        border-color: #1a1a1a;
        background-color: #1a1a1a;
        color: white;
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: white !important;
        border-radius: 8px !important;
        border: 1px solid #eee !important;
    }
    </style>
    """, unsafe_allow_items=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]

# Header
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
c_search, c_sort = st.columns([2, 1])
search_query = c_search.text_input("", placeholder="🔍 Search prospects...")
view_mode = c_sort.selectbox("Layout", ["Group by Status", "List View"])

try:
    response = supabase.table("prospects").select("*").order("name").execute()
    prospects = response.data
except:
    prospects = []

if prospects:
    if search_query:
        prospects = [p for p in prospects if search_query.lower() in p.get('name', '').lower()]

    if view_mode == "Group by Status":
        for s in MY_STATUSES:
            stage_leads = [p for p in prospects if p.get('stage') == s]
            if stage_leads:
                st.markdown(f"#### {s}")
                for p in stage_leads:
                    p_id = p.get('id')
                    # Custom HTML for the "Card" feel
                    with st.container():
                        st.markdown(f"""
                        <div class="status-card">
                            <span style="font-size: 1.1rem; font-weight: 700;">{p.get('name')}</span><br>
                            <span style="color: #666; font-size: 0.9rem;">{p.get('phone')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_edit, col_del = st.columns([5, 1])
                        with col_edit.expander("View details & edit"):
                            new_stage = st.selectbox("Status", MY_STATUSES, index=MY_STATUSES.index(p.get('stage')), key=f"s_{p_id}")
                            new_notes = st.text_area("Notes", value=p.get('notes', ''), key=f"n_{p_id}")
                            if st.button("Update", key=f"up_{p_id}"):
                                supabase.table("prospects").update({"stage": new_stage, "notes": new_notes}).eq("id", p_id).execute()
                                st.rerun()
                        
                        if col_del.button("🗑️", key=f"del_{p_id}"):
                            supabase.table("prospects").delete().eq("id", p_id).execute()
                            st.rerun()
    else:
        for p in prospects:
            st.write(f"**{p.get('name')}** — {p.get('stage')}")

else:
    st.info("No active prospects.")
