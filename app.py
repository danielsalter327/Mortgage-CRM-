import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Mortgage Prospect Tracker", layout="wide")

# 1. Simple Data Storage (In a real app, you'd link this to a Google Sheet or Database)
if 'leads' not in st.session_state:
    st.session_state.leads = pd.DataFrame(columns=[
        "Name", "Loan Amount", "Stage", "Credit Score", "Last Contact"
    ])

st.title("🏠 Mortgage Prospect CRM")

# --- SIDEBAR: Add New Prospect ---
with st.sidebar:
    st.header("Add New Lead")
    name = st.text_input("Full Name")
    amount = st.number_input("Estimated Loan Amount ($)", min_value=0, step=10000)
    score = st.slider("Estimated Credit Score", 300, 850, 700)
    stage = st.selectbox("Current Stage", ["New Lead", "Prequalified", "In Processing", "Application Submitted"])
    
    if st.button("Add to Pipeline"):
        new_data = pd.DataFrame({
            "Name": [name], 
            "Loan Amount": [amount], 
            "Stage": [stage], 
            "Credit Score": [score],
            "Last Contact": [datetime.now().strftime("%Y-%m-%d")]
        })
        st.session_state.leads = pd.concat([st.session_state.leads, new_data], ignore_index=True)
        st.success(f"Added {name}!")

# --- MAIN DASHBOARD ---
col1, col2, col3 = st.columns(3)
total_pipeline = st.session_state.leads["Loan Amount"].sum()
app_count = len(st.session_state.leads[st.session_state.leads["Stage"] == "Application Submitted"])

col1.metric("Total Pipeline Value", f"${total_pipeline:,.0f}")
col2.metric("Active Prospects", len(st.session_state.leads))
col3.metric("Applications Reached", app_count)

st.subheader("Current Pipeline")
st.dataframe(st.session_state.leads, use_container_width=True)

# --- KANBAN VIEW (Simplified) ---
st.subheader("Stages Overview")
cols = st.columns(4)
stages = ["New Lead", "Prequalified", "In Processing", "Application Submitted"]

for i, s in enumerate(stages):
    with cols[i]:
        st.markdown(f"**{s}**")
        names = st.session_state.leads[st.session_state.leads["Stage"] == s]["Name"].tolist()
        for n in names:
            st.info(n)
