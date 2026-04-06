import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1 { font-weight: 800 !important; color: #111; letter-spacing: -1.5px; margin-bottom: 0px !important; }
    .header-potential { color: #E6B800; border-bottom: 2px solid #E6B800; font-weight: 700; margin-top: 2rem !important; }
    .header-started { color: #28a745; border-bottom: 2px solid #28a745; font-weight: 700; margin-top: 2rem !important; }
    .header-trid { color: #dc3545; border-bottom: 2px solid #dc3545; font-weight: 700; margin-top: 2rem !important; }
    .header-processing { color: #007bff; border-bottom: 2px solid #007bff; font-weight: 700; margin-top: 2rem !important; }
    
    .task-box { background-color: #fdfdfd; border: 1px solid #eee; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .task-future { background-color: #f8f9fa; border: 1px solid #e9ecef; border-left: 6px solid #adb5bd; padding: 12px; border-radius: 8px; margin-bottom: 8px; }
    
    .task-potential { border-left: 6px solid #E6B800; }
    .task-started { border-left: 6px solid #28a745; }
    .task-trid { border-left: 6px solid #dc3545; }
    .task-processing { border-left: 6px solid #007bff; }
    
    .crm-card { background-color: #fff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 600; font-size: 1rem; border: 1px solid #eef2ff; padding: 4px 8px; border-radius: 6px; background: #f8faff; }
    .notes-box { color: #555; font-size: 0.95rem; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; padding-left: 20px; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]
COLOR_MAP = {"Potential Lead": "header-potential", "Started Application": "header-started", "Trid Triggered": "header-trid", "In Processing": "header-processing"}
TASK_COLOR_MAP = {"Potential Lead": "task-potential", "Started Application": "task-started", "Trid Triggered": "task-trid", "In Processing": "task-processing"}

st.title("Mortgage CRM")

# --- ADD NEW LEAD ---
with st.expander("➕ CREATE NEW LEAD", expanded=False):
    with st.form("new_lead_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n, p = c1.text_input("Full Name"), c2.text_input("Phone")
        s, note = c1.selectbox("Initial Status", MY_STATUSES), st.text_area("Notes")
        if st.form_submit_button("Add Lead"):
            if n and p:
                supabase.table("prospects").insert({"name": n, "phone": p, "stage": s, "notes": note}).execute()
                st.rerun()

st.markdown("---")

# --- SECTION 1: DUE TODAY ---
st.subheader("📋 Due Today")
try:
    today_str = date.today().isoformat()
    # Fetch incomplete tasks due today or before
    task_resp = supabase.table("tasks").select("*, prospects(name, phone, stage)").eq("is_completed", False).lte("due_date", today_str).order("due_date").execute()
    tasks_today = task_resp.data
    
    if tasks_today:
        for t in tasks_today:
            p_info = t.get('prospects', {})
            p_name, p_phone, p_stage = p_info.get('name', 'Lead'), p_info.get('phone', ''), p_info.get('stage', 'Potential Lead')
            raw_phone = "".join(filter(str.isdigit, p_phone))
            task_css = TASK_COLOR_MAP.get(p_stage, "task-potential")

            st.markdown(f"""
                <div class="task-box {task_css}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="font-weight: 700; color: #111;">{p_name} <small style="color:red;">({t['due_date']})</small></div>
                            <div style="font-size: 0.75rem; color: #888;">📍 {p_stage}</div>
                            <div style="margin-top: 5px;"><b>Task:</b> {t['task_text']}</div>
                        </div>
                        <a href="tel:{raw_phone}" style="text-decoration: none; color: #0066ff; font-weight: 700;">📞 {p_phone}</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Complete", key=f"done_{t['id']}"):
                supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                st.rerun()
    else:
        st.info("No immediate tasks.")
except:
    st.caption("Syncing task engine...")

st.markdown("---")

# --- SECTION 2: PIPELINE ---
st.subheader("🏠 Pipeline")
search = st.text_input("", placeholder="🔍 Search leads...")
if 'filter' not in st.session_state: st.session_state.filter = "All"
f_cols = st.columns(len(MY_STATUSES) + 1)
if f_cols[0].button("Show All"): st.session_state.filter = "All"
for i, s in enumerate(MY_STATUSES):
    if f_cols[i+1].button(s): st.session_state.filter = s

try:
    data = supabase.table("prospects").select("*").order("name").execute().data
    if search: data = [p for p in data if search.lower() in p.get('name', '').lower()]
    
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
                    with c_task.expander("➕ Schedule Task"):
                        t_text = st.text_input("Task", key=f"t_in_{p_id}")
                        t_date = st.date_input("Date", value=date.today(), key=f"t_date_{p_id}")
                        if st.button("Set Schedule", key=f"t_btn_{p_id}"):
                            supabase.table("tasks").insert({"prospect_id": p_id, "task_text": t_text, "due_date": t_date.isoformat(), "is_completed": False}).execute()
                            st.rerun()
                    
                    with c_edit.expander("Update"):
                        ns = st.selectbox("Status", MY_STATUSES, index=MY_STATUSES.index(p['stage']), key=f"s_{p_id}")
                        nn = st.text_area("Notes", value=p['notes'], key=f"n_{p_id}")
                        if st.button("Save", key=f"up_{p_id}"):
                            supabase.table("prospects").update({"stage": ns, "notes": nn}).eq("id", p_id).execute()
                            st.rerun()
                    if c_del.button("🗑️", key=f"del_{p_id}"):
                        supabase.table("prospects").delete().eq("id", p_id).execute()
                        st.rerun()
except:
    st.info("Pipeline ready.")

st.markdown("---")

# --- SECTION 3: FUTURE TASKS ---
with st.expander("📅 VIEW UPCOMING SCHEDULE", expanded=False):
    try:
        # Fetch tasks due AFTER today
        future_resp = supabase.table("tasks").select("*, prospects(name, phone)").eq("is_completed", False).gt("due_date", today_str).order("due_date").execute()
        future_tasks = future_resp.data
        
        if future_tasks:
            for ft in future_tasks:
                st.markdown(f"""
                    <div class="task-future">
                        <b>{ft['due_date']}</b> — {ft.get('prospects', {}).get('name', 'Lead')}: {ft['task_text']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No future tasks scheduled.")
    except:
        st.write("Upcoming list pending...")
