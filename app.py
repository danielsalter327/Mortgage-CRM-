import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta

# 1. DATABASE CONNECTION
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- GLOBAL SETTINGS ---
MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]
COLOR_MAP = {"Potential Lead": "header-potential", "Started Application": "header-started", "Trid Triggered": "header-trid", "In Processing": "header-processing"}
TASK_COLOR_MAP = {"Potential Lead": "task-potential", "Started Application": "task-started", "Trid Triggered": "task-trid", "In Processing": "task-processing"}

# --- SHARED STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1 { font-weight: 800 !important; color: #111; letter-spacing: -1.5px; margin-bottom: 10px !important; }
    .header-potential { color: #E6B800; border-bottom: 2px solid #E6B800; font-weight: 700; margin-top: 2rem !important; }
    .header-started { color: #28a745; border-bottom: 2px solid #28a745; font-weight: 700; margin-top: 2rem !important; }
    .header-trid { color: #dc3545; border-bottom: 2px solid #dc3545; font-weight: 700; margin-top: 2rem !important; }
    .header-processing { color: #007bff; border-bottom: 2px solid #007bff; font-weight: 700; margin-top: 2rem !important; }
    .task-box { background-color: #fdfdfd; border: 1px solid #eee; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .task-potential { border-left: 6px solid #E6B800; }
    .task-started { border-left: 6px solid #28a745; }
    .task-trid { border-left: 6px solid #dc3545; }
    .task-processing { border-left: 6px solid #007bff; }
    .task-future-bar { border-left: 6px solid #adb5bd; }
    .crm-card { background-color: #fff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 600; font-size: 1rem; border: 1px solid #eef2ff; padding: 4px 8px; border-radius: 6px; background: #f8faff; }
    .notes-box { color: #555; font-size: 0.95rem; flex-grow: 1; border-left: 1px solid #eee; margin-left: 20px; padding-left: 20px; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

def fmt_date(iso_str):
    if not iso_str: return ""
    return datetime.strptime(iso_str, "%Y-%m-%d").strftime("%m/%d/%Y")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏠 Menu")
    page = st.radio("Go to:", ["📋 Tasks", "🏠 Pipeline", "➕ Add New Lead"])
    st.markdown("---")
    st.caption(f"Today: {date.today().strftime('%m/%d/%Y')}")

# --- PAGE 1: TASK DASHBOARD ---
if page == "📋 Tasks":
    st.title("Task Dashboard")
    t_today, t_upcoming = st.tabs(["Due Today / Overdue", "Upcoming Schedule"])
    today_str = date.today().isoformat()

    def display_task_list(data_list, is_today=True):
        for t in data_list:
            p = t.get('prospects', {})
            p_id = p.get('id')
            task_css = TASK_COLOR_MAP.get(p.get('stage'), "task-potential") if is_today else "task-future-bar"
            raw_phone = "".join(filter(str.isdigit, p.get('phone', '')))
            with st.container():
                st.markdown(f"""<div class="task-box {task_css}"><div style="display: flex; justify-content: space-between; align-items: flex-start;"><div><div style="font-weight: 700; color: #111;">{p.get('name')} <span style="color:{'red' if is_today else '#666'}; font-size:0.8rem;">({fmt_date(t['due_date'])})</span></div><div style="font-size: 0.75rem; color: #888;">📍 {p.get('stage')}</div><div style="margin-top: 5px;"><b>Task:</b> {t['task_text']}</div></div><a href="tel:{raw_phone}" style="text-decoration: none; color: #0066ff; font-weight: 700;">📞 {p.get('phone', 'No Phone')}</a></div></div>""", unsafe_allow_html=True)
                col1, col2 = st.columns([2, 4])
                with col1.expander("✅ Complete & Schedule Next"):
                    updated_note = st.text_area("Update Lead Notes:", value=p.get('notes', ''), key=f"note_up_{t['id']}")
                    do_follow_up = st.checkbox("Schedule another follow-up?", value=False, key=f"chk_fup_{t['id']}")
                    if do_follow_up:
                        c1, c2 = st.columns(2)
                        next_task = c1.text_input("Next Task:", value="Follow up call", key=f"fup_txt_{t['id']}")
                        next_date = c2.date_input("When?", value=date.today() + timedelta(days=1), key=f"fup_date_{t['id']}")
                    if st.button("Complete & Save", key=f"btn_comp_{t['id']}"):
                        supabase.table("prospects").update({"notes": updated_note}).eq("id", p_id).execute()
                        supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                        if do_follow_up:
                            supabase.table("tasks").insert({"prospect_id": p_id, "task_text": next_task, "due_date": next_date.isoformat(), "is_completed": False}).execute()
                        st.rerun()
                with col2.expander("Details"):
                    st.write(f"**Notes:** {p.get('notes', 'None')}")

    with t_today:
        task_resp = supabase.table("tasks").select("*, prospects(*)").eq("is_completed", False).lte("due_date", today_str).order("due_date").execute()
        if task_resp.data: display_task_list(task_resp.data, is_today=True)
        else: st.info("No tasks due today.")

    with t_upcoming:
        col_f1, _ = st.columns([2, 3])
        filter_date = col_f1.date_input("Filter by Date:", value=None, min_value=date.today() + timedelta(days=1))
        query = supabase.table("tasks").select("*, prospects(*)").eq("is_completed", False).gt("due_date", today_str).order("due_date")
        if filter_date: query = query.eq("due_date", filter_date.isoformat())
        future_resp = query.execute()
        if future_resp.data: display_task_list(future_resp.data, is_today=False)
        else: st.info("No upcoming tasks found.")

# --- PAGE 2: PIPELINE ---
elif page == "🏠 Pipeline":
    st.title("Mortgage Pipeline")
    search = st.text_input("", placeholder="🔍 Search leads...")
    
    if 'filter' not in st.session_state: st.session_state.filter = "All"
    f_cols = st.columns(len(MY_STATUSES) + 1)
    if f_cols[0].button("All"): st.session_state.filter = "All"
    for i, s in enumerate(MY_STATUSES):
        if f_cols[i+1].button(s): st.session_state.filter = s

    try:
        resp = supabase.table("prospects").select("*").order("name").execute()
        data = resp.data
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
                        c_t, c_e, c_d = st.columns([2, 1, 1])
                        with c_t.expander("➕ Schedule Task"):
                            t_txt = st.text_input("Task", key=f"ti_{p_id}")
                            t_dt = st.date_input("Date", value=date.today(), key=f"td_{p_id}")
                            if st.button("Set Schedule", key=f"tb_{p_id}"):
                                supabase.table("tasks").insert({"prospect_id": p_id, "task_text": t_txt, "due_date": t_dt.isoformat(), "is_completed": False}).execute()
                                st.rerun()
                        with c_e.expander("Update"):
                            ns = st.selectbox("Status", MY_STATUSES, index=MY_STATUSES.index(p['stage']), key=f"s_{p_id}")
                            nn = st.text_area("Notes", value=p['notes'], key=f"n_{p_id}")
                            if st.button("Save", key=f"up_{p_id}"):
                                supabase.table("prospects").update({"stage": ns, "notes": nn}).eq("id", p_id).execute()
                                st.rerun()
                        if c_d.button("🗑️", key=f"del_{p_id}"):
                            supabase.table("tasks").delete().eq("prospect_id", p_id).execute()
                            supabase.table("prospects").delete().eq("id", p_id).execute()
                            st.rerun()
    except Exception as e: st.error(f"Error loading pipeline: {e}")

# --- PAGE 3: ADD NEW LEAD (WITH COMBINED TASK) ---
elif page == "➕ Add New Lead":
    st.title("Create New Lead")
    with st.form("new_lead_form", clear_on_submit=True):
        st.subheader("👤 Lead Information")
        c1, c2 = st.columns(2)
        n = c1.text_input("Full Name")
        p = c2.text_input("Phone Number")
        s = c1.selectbox("Status", MY_STATUSES)
        note = st.text_area("Initial Notes")
        
        st.markdown("---")
        st.subheader("📅 Initial Task (Optional)")
        t_text = st.text_input("Task Description (e.g., 'Initial Follow-up')")
        t_date = st.date_input("Task Due Date", value=date.today())
        
        if st.form_submit_button("Confirm & Add to Pipeline"):
            if n and p:
                # 1. Create Lead
                lead_resp = supabase.table("prospects").insert({
                    "name": n, 
                    "phone": p, 
                    "stage": s, 
                    "notes": note
                }).execute()
                
                # 2. If Task text is provided, create task
                if t_text and lead_resp.data:
                    new_id = lead_resp.data[0]['id']
                    supabase.table("tasks").insert({
                        "prospect_id": new_id,
                        "task_text": t_text,
                        "due_date": t_date.isoformat(),
                        "is_completed": False
                    }).execute()
                
                st.success(f"Successfully added {n}!")
            else:
                st.error("Full Name and Phone Number are required.")
