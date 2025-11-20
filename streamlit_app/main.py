"""
PV Test Report Automation System - Main Streamlit Application
ISO 17025 / NABL Compliant Test Report Generation
"""

import streamlit as st
import os
from pathlib import Path

# Import page modules
from pages import (
    dashboard,
    protocol_selection,
    data_upload,
    test_execution,
    review_workflow,
    report_generation,
    equipment_management,
    calibration_tracking,
    audit_trail
)

# Configure page
st.set_page_config(
    page_title="PV Test Automation System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ganeshgowri-ASA/pv-test-report-automation',
        'Report a bug': 'https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues',
        'About': """
        # PV Test Report Automation System

        World-class photovoltaic test lab report automation system.

        **Standards Compliance:**
        - IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
        - ISO 17025 / NABL / ILAC / BIS

        **Version:** 1.0.0
        """
    }
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .accreditation-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        background-color: #e8f4f8;
        border: 2px solid #1f77b4;
        border-radius: 8px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #155a8a;
        border-color: #155a8a;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'current_project' not in st.session_state:
    st.session_state.current_project = None

def show_accreditation_info():
    """Display accreditation and compliance information"""
    accreditation_num = os.getenv('ACCREDITATION_NUMBER', 'NABL-XXXXX')

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏆 Accreditation")
    st.sidebar.info(f"""
    **NABL:** {accreditation_num}
    **ISO/IEC 17025:2017**
    **ILAC-MRA Signatory**
    """)

def render_login():
    """Simple login interface"""
    st.markdown('<div class="main-header">⚡ PV Test Automation System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ISO 17025 Compliant Test Report Generation</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 User Authentication")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🔓 Login", use_container_width=True):
                # Simple authentication (replace with proper auth in production)
                if username and password:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Engineer"  # Default role
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Please enter valid credentials")

        with col_b:
            if st.button("👤 Guest Access", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.user_role = "Guest"
                st.session_state.username = "Guest"
                st.rerun()

        st.markdown("---")
        st.info("""
        **System Features:**
        - 8 IEC Protocol Standards
        - 9 Test Block Modules
        - LLM-Powered Analysis
        - Multi-Format Export
        - Complete Traceability
        - Reviewer/Approver Workflow
        """)

def main():
    """Main application logic"""

    # Check authentication
    if not st.session_state.authenticated:
        render_login()
        return

    # Sidebar navigation
    st.sidebar.title("⚡ PV Test Automation")
    st.sidebar.markdown(f"**User:** {st.session_state.get('username', 'Unknown')}")
    st.sidebar.markdown(f"**Role:** {st.session_state.get('user_role', 'Unknown')}")
    st.sidebar.markdown("---")

    # Navigation pages
    pages = {
        "🏠 Dashboard": dashboard.render,
        "📋 Protocol Selection": protocol_selection.render,
        "📤 Data Upload": data_upload.render,
        "⚙️ Test Execution": test_execution.render,
        "✅ Review Workflow": review_workflow.render,
        "📄 Report Generation": report_generation.render,
        "🔧 Equipment Management": equipment_management.render,
        "📅 Calibration Tracking": calibration_tracking.render,
        "🔍 Audit Trail": audit_trail.render,
    }

    selection = st.sidebar.radio("Navigation", list(pages.keys()))

    show_accreditation_info()

    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.rerun()

    # Render selected page
    try:
        pages[selection]()
    except Exception as e:
        st.error(f"Error rendering page: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
