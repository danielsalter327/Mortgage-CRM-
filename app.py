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
    h1 { font-weight: 800 !important; color: #111; letter-spacing: -1.5px; }
    .header-potential { color: #E6B800; border-bottom: 2px solid #E6B800; font-weight: 700; margin-top: 2rem !important; }
    .header-started { color: #28a745; border-bottom: 2px solid #28a745; font-weight: 700; margin-top: 2rem !important; }
    .header-trid { color: #dc3545; border-bottom: 2px solid #dc3545; font-weight: 700; margin-top: 2rem !important; }
    .header-processing { color: #007bff; border-bottom: 2px solid #007bff; font-weight: 700; margin-top: 2rem !important; }
    .crm-card { background-color: #fff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 600; font-size: 1rem; border: 1px solid #eef2ff; padding: 4px 8px; border-radius: 6px; background: #f8faff; }
    .notes-box { color: #555; font-size: 0.95rem; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; padding-left: 20px; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]
COLOR_MAP = {"Potential Lead": "header-potential", "Started Application": "header-started", "Trid Triggered": "header-trid", "In Processing": "header-processing"}

st.title("Mortgage CRM")

# --- SECTION: GLOBAL TASKS (Aggressive Fetch) ---
st.subheader("📋 Pending Tasks")
try:
    # We fetch ALL tasks from the table to see if anything is there
    task_resp = supabase.table("tasks").select("*").execute()
    all_tasks = task_resp.data
    
    # Filter for incomplete ones in Python (bypassing DB filters for safety)
    pending = [t for t in all_tasks if t.get('is_completed') == False]
    
    if pending:
        for t in pending:
            with st.container(border=True):
                col_t, col_b = st.columns([5, 1])
                col_t.markdown(f"🔔 **ACTION:** {t['task_text']}")
                if col_b.button("Done", key=f"done_{t['id']}"):
                    supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                    st.rerun()
    else:
        st.info("No pending tasks. If you just added one, refresh the page.")
        # Debugging line: tells us if there are ANY rows in the table at all
        if len(all_tasks) > 0:
            st.caption(f"Note: Found {len(all_tasks)} completed tasks in database.")
except Exception as e:
    st.error(f"Waiting for Supabase to sync... ({e})")

st.markdown("---")

# --- PIPELINE FILTERS ---
if 'filter' not in st.session_state: st.session_state.filter = "All"
f_cols = st.columns(len(MY_STATUSES) + 1)
if f_cols[0].button("Show All"): st.session_state.filter = "All"
for i, s in enumerate(MY_STATUSES):
    if f_cols[i+1].button(s): st.session_state.filter = s

# --- PIPELINE DATA ---
search = st.text_input("", placeholder="🔍 Search by name...")

try:
    data = supabase.table("prospects").select("*").order("name").execute().data
    if search:
        data = [p for p in data if search.lower() in p.get('name', '').lower()]
    
    for s in MY_STATUSES:
        if st.session_state.filter != "All" and st.session_state.filter != s: continue
        leads = [p for p in data if p.get('stage') == s]
        if leads:
            st.markdown(f'<div class="{COLOR_MAP.get(s)}">{s.upper()} ({len(leads)})</div>', unsafe_allow_html=True)
            for p in leads:
                p_id = p.get('id')
                raw_phone = "".join(filter(str.isdigit, p.get('phone', '')))
                with st.container():
                    st.markdown(f'<div class="crm-card"><div style="min-width: 180px;"><div class="name-text">{p["name"]}</div><a href="tel:{raw_phone}" class="phone-link">📞 {p["phone"]}</a></div><div class="notes-box">{p["notes"] if p["notes"] else "..." }</div></div>', unsafe_allow_html=True)
                    
                    c_task, c_edit, c_del = st.columns([2, 1, 1])
                    with c_task.expander("➕ Add Task"):
                        t_text = st.text_input("Task detail", key=f"t_in_{p_id}")
                        if st.button("Save Task", key=f"t_btn_{p_id}"):
                            # We send it to the DB
                            supabase.table("tasks").insert({
                                "prospect_id": p_id, 
                                "task_text": t_text, 
                                "is_completed": False
                            }).execute()
                            st.rerun()
                    
                    with c_edit.expander("Edit"):
                        new_s = st.selectbox("Status", MY_STATUSES, index=MY_STATUSES.index(p['stage']), key=f"s_{p_id}")
                        new_n = st.text_area("Notes", value=p['notes'], key=f"n_{p_id}")
                        if st.button("Save", key=f"up_{p_id}"):
                            supabase.table("prospects").update({"stage": new_s, "notes": new_n}).eq("id", p_id).execute()
                            st.rerun()
                    
                    if c_del.button("🗑️", key=f"del_{p_id}"):
                        supabase.table("prospects").delete().eq("id", p_id).execute()
                        st.rerun()
except Exception as e:
    st.info("Pipeline is ready.")
