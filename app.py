import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage CRM", layout="wide", page_icon="🏠")

# --- STYLING (Standardized for Performance) ---
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
    
    .name-text { font-size: 1.1rem; font-weight: 700; color: #111; }
    .phone-link { color: #0066ff !important; text-decoration: none !important; font-weight: 600; font-size: 1rem; border: 1px solid #eef2ff; padding: 4px 8px; border-radius: 6px; background: #f8faff; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

MY_STATUSES = ["Potential Lead", "Started Application", "Trid Triggered", "In Processing"]
TASK_COLOR_MAP = {"Potential Lead": "task-potential", "Started Application": "task-started", "Trid Triggered": "task-trid", "In Processing": "task-processing"}

def fmt_date(iso_str):
    if not iso_str: return ""
    return datetime.strptime(iso_str, "%Y-%m-%d").strftime("%m/%d/%Y")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏠 Menu")
    page = st.radio("Go to:", ["📋 Tasks", "🏠 Pipeline", "➕ Add New Lead"])

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
                st.markdown(f"""<div class="task-box {task_css}"><div style="display: flex; justify-content: space-between; align-items: flex-start;"><div><div style="font-weight: 700; color: #111;">{p.get('name')} <span style="color:{'red' if is_today else '#666'}; font-size:0.8rem;">({fmt_date(t['due_date'])})</span></div><div style="font-size: 0.75rem; color: #888;">📍 {p.get('stage')}</div><div style="margin-top: 5px;"><b>Task:</b> {t['task_text']}</div></div><a href="tel:{raw_phone}" style="text-decoration: none; color: #0066ff; font-weight: 700;">📞 {p.get('phone')}</a></div></div>""", unsafe_allow_html=True)
                
                # RE-SCHEDULE LOGIC
                with st.expander("✅ Complete & Schedule Next"):
                    # Section A: Update Notes
                    current_notes = p.get('notes', '')
                    updated_note = st.text_area("Update Lead Notes:", value=current_notes, key=f"note_up_{t['id']}")
                    
                    st.markdown("---")
                    
                    # Section B: Optional Follow-up
                    do_follow_up = st.checkbox("Schedule another follow-up task?", value=False, key=f"chk_fup_{t['id']}")
                    
                    if do_follow_up:
                        c1, c2 = st.columns(2)
                        next_task = c1.text_input("Next Task:", value="Follow up call", key=f"fup_txt_{t['id']}")
                        next_date = c2.date_input("When?", value=date.today() + timedelta(days=1), key=f"fup_date_{t['id']}")
                    
                    if st.button("Complete & Save", key=f"btn_comp_{t['id']}"):
                        # 1. Update Lead Notes
                        supabase.table("prospects").update({"notes": updated_note}).eq("id", p_id).execute()
                        
                        # 2. Mark current task done
                        supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                        
                        # 3. Create NEW task if requested
                        if do_follow_up:
                            supabase.table("tasks").insert({
                                "prospect_id": p_id,
                                "task_text": next_task,
                                "due_date": next_date.isoformat(),
                                "is_completed": False
                            }).execute()
                        
                        st.success("Updated!")
                        st.rerun()

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
        else: st.info("No upcoming tasks.")

# --- PIPELINE & ADD LEAD PAGES (Logic remains the same as previous) ---
elif page == "🏠 Pipeline":
    st.title("Mortgage Pipeline")
    # ... (Standard pipeline code from previous turn)
    search = st.text_input("", placeholder="🔍 Search leads...")
    resp = supabase.table("prospects").select("*").order("name").execute()
    data = resp.data
    if search: data = [p for p in data if search.lower() in p.get('name', '').lower()]
    for s in MY_STATUSES:
        leads = [p for p in data if p.get('stage') == s]
        if leads:
            st.markdown(f'<div class="{COLOR_MAP.get(s)}">{s.upper()} ({len(leads)})</div>', unsafe_allow_html=True)
            for p in leads:
                with st.container():
                    st.write(f"**{p['name']}**")
                    # (Standard Edit/Task/Delete buttons)
                    # Note: Keeping this section brief to focus on your new Task feature
elif page == "➕ Add New Lead":
    st.title("Create New Lead")
    # ... (Standard Form code from previous turn)
