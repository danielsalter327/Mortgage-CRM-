import streamlit as st
from supabase import create_client, Client

# 1. Setup Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Mortgage Vault CRM", layout="wide")

st.title("🏦 Mortgage Vault CRM")

# --- ADD PROSPECT ---
with st.expander("➕ Add New Prospect"):
    with st.form("prospect_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name")
        phone = col2.text_input("Phone")
        amount = col1.number_input("Loan Amount", step=1000)
        stage = col2.selectbox("Stage", ["New Lead", "Prequalified", "In Processing", "Application"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Securely Save"):
            data = {"name": name, "phone": phone, "amount": amount, "stage": stage, "notes": notes}
            supabase.table("prospects").insert(data).execute()
            st.success(f"Saved {name} to the Vault!")
            st.rerun()

# --- VIEW PIPELINE ---
st.subheader("Your Active Pipeline")
# We fetch 'id' now so we know exactly which one to delete
response = supabase.table("prospects").select("*").order("name").execute()
prospects = response.data

if prospects:
    for p in prospects:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            
            c1.write(f"**{p['name']}** ({p['stage']})")
            c2.markdown(f"📞 [Call {p['phone']}](tel:{p['phone']})")
            c3.write(f"${p['amount']:,}")
            
            # THE DELETE FUNCTION
            # We use the unique 'id' from Supabase to ensure we delete the right person
            if c4.button("🗑️ Delete", key=f"delete_{p['id']}"):
                supabase.table("prospects").delete().eq("id", p["id"]).execute()
                st.warning(f"Removed {p['name']} from the Vault.")
                st.rerun()
            
            if p.get('notes'):
                st.caption(f"📝 **Notes:** {p['notes']}")
else:
    st.info("No prospects in the vault yet.")
