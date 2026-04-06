import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

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

def fmt_date(iso_str):
    if not iso_str: return ""
    return datetime.strptime(iso_str, "%Y-%m-%d").strftime("%m/%d/%Y")

# --- SIDEBAR NAVIGATION ---
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

    with t_today:
        task_resp = supabase.table("tasks").select("*, prospects(*)").eq("is_completed", False).lte("due_date", today_str).order("due_date").execute()
        if task_resp.data:
            for t in task_resp.data:
                p = t.get('prospects', {})
                task_css = TASK_COLOR_MAP.get(p.get('stage'), "task-potential")
                raw_phone = "".join(filter(str.isdigit, p.get('phone', '')))
                with st.container():
                    st.markdown(f"""<div class="task-box {task_css}"><div style="display: flex; justify-content: space-between; align-items: flex-start;"><div><div style="font-weight: 700; color: #111;">{p.get('name')} <span style="color:red; font-size:0.8rem;">({fmt_date(t['due_date'])})</span></div><div style="font-size: 0.75rem; color: #888;">📍 {p.get('stage')}</div><div style="margin-top: 5px;"><b>Task:</b> {t['task_text']}</div></div><a href="tel:{raw_phone}" style="text-decoration: none; color: #0066ff; font-weight: 700;">📞 {p.get('phone')}</a></div></div>""", unsafe_allow_html=True)
                    c1, c2 = st.columns([1, 5])
                    if c1.button("Done", key=f"d_tod_{t['id']}"):
                        supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                        st.rerun()
                    with c2.expander("View Lead Details"):
                        st.write(f"**Lead Notes:** {p.get('notes', 'None')}")
        else:
            st.info("No tasks due today.")

    with t_upcoming:
        future_resp = supabase.table("tasks").select("*, prospects(*)").eq("is_completed", False).gt("due_date", today_str).order("due_date").execute()
        if future_resp.data:
            for t in future_resp.data:
                p = t.get('prospects', {})
                raw_phone = "".join(filter(str.isdigit, p.get('phone', '')))
                with st.container():
                    st.markdown(f"""<div class="task-box" style="border-left: 6px solid #adb5bd;"><div style="display: flex; justify-content: space-between; align-items: flex-start;"><div><div style="font-weight: 700;">{p.get('name')} <span style="color:#666; font-size:0.8rem;">({fmt_date(t['due_date'])})</span></div><div><b>Task:</b> {t['task_text']}</div></div><a href="tel:{raw_phone}" style="text-decoration: none; color: #0066ff; font-weight: 700;">📞 {p.get('phone')}</a></div></div>""", unsafe_allow_html=True)
                    with st.expander("Details"):
                        st.write(f"**Status:** {p.get('stage')} | **Notes:** {p.get('notes', 'None')}")
        else:
            st.info("No future tasks scheduled.")

# --- PAGE 2: PIPELINE ---
elif page == "🏠 Pipeline":
    st.title("Mortgage Pipeline")
    search = st.text_input("", placeholder="🔍 Search leads...")
    if 'filter' not in st.session_state: st.session_state.filter = "All"
    f_cols = st.columns(len(MY_STATUSES) + 1)
    if f_cols[0].button("All"): st.session_state.filter = "All"
    for i, s in enumerate(MY_STATUSES):
        if f_cols[i+1].button(s): st.session_state.filter = s

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
                        supabase.table("prospects").delete().eq("id", p_id).execute()
                        st.rerun()

# --- PAGE 3: ADD NEW LEAD ---
elif page == "➕ Add New Lead":
    st.title("Create New Lead")
    with st.form("new_lead_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n, p = c1.text_input("Full Name"), c2.text_input("Phone")
        s, note = c1.selectbox("Initial Status", MY_STATUSES), st.text_area("Notes")
        if st.form_submit_button("Add to Pipeline"):
            if n and p:
                supabase.table("prospects").insert({"name": n, "phone": p, "stage": s, "notes": note}).execute()
                st.success(f"Added {n}!")
            else:
                st.error("Name and Phone required.")
