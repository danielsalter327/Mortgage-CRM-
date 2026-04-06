# --- SECTION: GLOBAL TASKS (Simplified for Troubleshooting) ---
st.subheader("📋 Pending Tasks")
try:
    # Fetch tasks - we removed the 'join' to make it simpler
    task_resp = supabase.table("tasks").select("*").eq("is_completed", False).execute()
    tasks_data = task_resp.data
    
    if tasks_data:
        for t in tasks_data:
            with st.container(border=True):
                col_t, col_b = st.columns([5, 1])
                
                # We just show the task text for now to prove it works
                col_t.markdown(f"🔔 **Task:** {t['task_text']}")
                
                if col_b.button("Done", key=f"done_{t['id']}"):
                    supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                    st.rerun()
    else:
        st.info("No pending tasks. You're all caught up!")
except Exception as e:
    # This will now tell us the EXACT error if it fails
    st.error(f"Database says: {e}")
