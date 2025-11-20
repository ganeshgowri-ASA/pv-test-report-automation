"""
Equipment Management - Track and manage test equipment
"""

import streamlit as st
import pandas as pd

def render():
    """Render equipment management page"""
    st.title("🔧 Equipment Management")
    st.markdown("### Test Equipment Tracking & Maintenance")

    # Equipment overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Equipment", "34")

    with col2:
        st.metric("Operational", "28", delta="82%")

    with col3:
        st.metric("Calibration Due", "3", delta="-2")

    with col4:
        st.metric("In Maintenance", "2")

    st.markdown("---")

    # Equipment list
    st.subheader("📋 Equipment Inventory")

    equipment_data = {
        "Equipment ID": ["EQ-001", "EQ-002", "EQ-003", "EQ-004", "EQ-005"],
        "Name": ["Solar Simulator", "I-V Curve Tracer", "EL Imaging System", "Insulation Tester", "Data Logger"],
        "Status": ["✅ Operational", "✅ Operational", "⚠️ Cal. Due", "🔧 Maintenance", "✅ Operational"],
        "Last Calibration": ["2024-10-15", "2024-09-20", "2024-05-10", "2024-08-01", "2024-11-01"],
        "Next Calibration": ["2025-10-15", "2025-09-20", "2024-11-10", "2025-08-01", "2025-11-01"],
        "Location": ["Lab-A", "Lab-A", "Lab-B", "Service", "Lab-C"]
    }

    df = pd.DataFrame(equipment_data)

    # Filter options
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        status_filter = st.selectbox("Status", ["All", "Operational", "Calibration Due", "Maintenance"])

    with col_f2:
        location_filter = st.selectbox("Location", ["All", "Lab-A", "Lab-B", "Lab-C", "Service"])

    with col_f3:
        search = st.text_input("Search Equipment", placeholder="EQ-XXX or name")

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Equipment details
    st.markdown("---")
    st.subheader("🔍 Equipment Details: Solar Simulator (EQ-001)")

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Specifications", "📅 Calibration", "🔧 Maintenance", "📊 Usage History"])

    with tab1:
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.markdown("""
            **General Information:**
            - Equipment ID: EQ-001
            - Name: Solar Simulator
            - Manufacturer: SolarTech Pro
            - Model: ST-AAA-5000
            - Serial Number: SN-2021-5489
            - Purchase Date: 2021-03-15
            """)

        with col_s2:
            st.markdown("""
            **Technical Specifications:**
            - Irradiance: 1000 W/m² ± 2%
            - Spectral Match: Class A (IEC 60904-9)
            - Non-uniformity: <2%
            - Temporal Stability: <1%
            - Test Area: 2m × 1.2m
            """)

    with tab2:
        st.markdown("**Calibration History:**")

        cal_data = pd.DataFrame({
            "Date": ["2024-10-15", "2023-10-10", "2022-10-05"],
            "Certificate No.": ["CAL-2024-1547", "CAL-2023-1289", "CAL-2022-0945"],
            "Calibration Lab": ["National Lab", "National Lab", "National Lab"],
            "Valid Until": ["2025-10-15", "2024-10-10", "2023-10-05"],
            "Status": ["✅ Valid", "Expired", "Expired"]
        })

        st.dataframe(cal_data, use_container_width=True, hide_index=True)

        if st.button("📄 View Current Certificate"):
            st.info("Opening calibration certificate...")

    with tab3:
        st.markdown("**Maintenance Log:**")

        maint_data = pd.DataFrame({
            "Date": ["2024-09-20", "2024-06-15", "2024-03-10"],
            "Type": ["Preventive", "Corrective", "Preventive"],
            "Description": ["Lamp replacement", "Fan motor repair", "General cleaning"],
            "Technician": ["Tech-A", "Tech-B", "Tech-A"],
            "Status": ["Completed", "Completed", "Completed"]
        })

        st.dataframe(maint_data, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("**Usage Statistics:**")

        col_u1, col_u2, col_u3 = st.columns(3)

        with col_u1:
            st.metric("Total Tests", "1,247")

        with col_u2:
            st.metric("Operating Hours", "3,458")

        with col_u3:
            st.metric("Avg. Tests/Month", "104")

    # Actions
    st.markdown("---")
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)

    with col_a1:
        if st.button("➕ Add Equipment", use_container_width=True):
            st.info("Add new equipment form")

    with col_a2:
        if st.button("📅 Schedule Calibration", use_container_width=True):
            st.info("Calibration scheduling")

    with col_a3:
        if st.button("🔧 Log Maintenance", use_container_width=True):
            st.info("Maintenance logging form")

    with col_a4:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Equipment report generation")
