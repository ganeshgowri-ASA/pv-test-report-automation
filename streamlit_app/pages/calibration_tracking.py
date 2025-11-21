"""
Calibration Tracking - Monitor equipment calibration schedules
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render():
    """Render calibration tracking page"""
    st.title("📅 Calibration Tracking")
    st.markdown("### Equipment Calibration Schedule & Certificate Management")

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Due This Month", "3", delta="-1")

    with col2:
        st.metric("Due Next Month", "5")

    with col3:
        st.metric("Overdue", "0", delta_color="inverse")

    with col4:
        st.metric("Valid Certificates", "28")

    st.markdown("---")

    # Calendar view
    st.subheader("📅 Calibration Schedule")

    view_mode = st.radio("View Mode", ["Calendar", "List", "Timeline"], horizontal=True)

    if view_mode == "List":
        cal_schedule = pd.DataFrame({
            "Equipment ID": ["EQ-003", "EQ-007", "EQ-012", "EQ-001", "EQ-002"],
            "Equipment Name": ["EL Imaging System", "Thermocouples Set", "Multimeter", "Solar Simulator", "I-V Curve Tracer"],
            "Last Cal Date": ["2024-05-10", "2024-07-15", "2024-08-20", "2024-10-15", "2024-09-20"],
            "Due Date": ["2024-11-10", "2025-01-15", "2025-02-20", "2025-10-15", "2025-09-20"],
            "Days Until Due": ["-10", "56", "92", "330", "304"],
            "Status": ["⚠️ Overdue", "✅ OK", "✅ OK", "✅ OK", "✅ OK"]
        })

        st.dataframe(cal_schedule, use_container_width=True, hide_index=True)

    # Alerts
    st.markdown("---")
    st.subheader("⚠️ Calibration Alerts")

    st.warning("**⚠️ EQ-003 (EL Imaging System):** Calibration overdue by 10 days!")
    st.info("**📅 EQ-007 (Thermocouples Set):** Calibration due in 56 days")
    st.info("**📅 EQ-012 (Multimeter):** Calibration due in 92 days")

    # Certificate management
    st.markdown("---")
    st.subheader("📄 Calibration Certificates")

    cert_data = pd.DataFrame({
        "Certificate No.": ["CAL-2024-1547", "CAL-2024-1423", "CAL-2024-1289"],
        "Equipment": ["EQ-001", "EQ-002", "EQ-004"],
        "Issue Date": ["2024-10-15", "2024-09-20", "2024-08-01"],
        "Valid Until": ["2025-10-15", "2025-09-20", "2025-08-01"],
        "Calibration Lab": ["National Lab", "National Lab", "Accredited Lab B"],
        "Traceability": ["NIST", "NIST", "PTB"]
    })

    st.dataframe(cert_data, use_container_width=True, hide_index=True)

    # Upload certificate
    st.markdown("---")
    st.subheader("📤 Upload Calibration Certificate")

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        equipment_select = st.selectbox("Select Equipment", ["EQ-001", "EQ-002", "EQ-003", "EQ-004"])
        cert_file = st.file_uploader("Upload Certificate (PDF)", type=["pdf"])

    with col_u2:
        cert_number = st.text_input("Certificate Number")
        issue_date = st.date_input("Issue Date")
        valid_until = st.date_input("Valid Until")

    if st.button("📤 Upload Certificate", use_container_width=True):
        if cert_file and cert_number:
            st.success("✅ Certificate uploaded successfully!")

    # Actions
    st.markdown("---")
    col_a1, col_a2, col_a3 = st.columns(3)

    with col_a1:
        if st.button("📧 Send Reminders", use_container_width=True):
            st.success("Calibration reminders sent")

    with col_a2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Generating calibration status report...")

    with col_a3:
        if st.button("⬇️ Export Schedule", use_container_width=True):
            st.success("Schedule exported to Excel")
