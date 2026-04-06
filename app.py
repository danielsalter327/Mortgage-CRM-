# --- SECTION: GLOBAL TASKS (Updated Safety Version) ---
st.subheader("📋 Pending Tasks")
try:
    # We fetch tasks and try to 'join' with prospects
    task_resp = supabase.table("tasks").select("*, prospects(name)").eq("is_completed", False).execute()
    tasks_data = task_resp.data
    
    if tasks_data:
        for t in tasks_data:
            with st.container(border=True):
                col_t, col_b = st.columns([5, 1])
                
                # Try to get the name, fallback to "Unknown" if the link is broken
                p_info = t.get('prospects')
                p_name = p_info.get('name', 'Unknown Lead') if p_info else "Unknown Lead"
                
                col_t.markdown(f"**{p_name}**: {t['task_text']}")
                col_t.caption(f"Added: {t.get('created_at', '')[:10]}")
                
                if col_b.button("Done", key=f"done_{t['id']}"):
                    supabase.table("tasks").update({"is_completed": True}).eq("id", t['id']).execute()
                    st.rerun()
    else:
        st.info("No pending tasks. You're all caught up!")
except Exception as e:
    # If the database table doesn't exist or isn't linked, show this
    st.warning("Ensure the 'tasks' table is linked to 'prospects' in Supabase.")
    # st.write(e) # Uncomment this if you need to see the exact error
