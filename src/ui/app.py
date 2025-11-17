"""
Main Streamlit application for PV Test Report Automation
Entry point with multi-page navigation and session state management
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import page modules
from src.ui.pages.dashboard import render_dashboard
from src.ui.pages.upload import render_upload_page
from src.ui.pages.create_report import render_create_report_page
from src.ui.pages.review import render_review_page
from src.ui.pages.export import render_export_page


# Page configuration
st.set_page_config(
    page_title="PV Test Report Automation",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': '# PV Test Report Automation\nVersion 1.0.0 - Phase 1'
    }
)


def initialize_session_state():
    """Initialize session state variables"""

    # Current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Authentication (placeholder for future)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Set to True for Phase 1

    if 'username' not in st.session_state:
        st.session_state.username = "demo_user"  # Placeholder

    # Data storage
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = {}

    if 'reports' not in st.session_state:
        st.session_state.reports = []

    # Settings
    if 'theme' not in st.session_state:
        st.session_state.theme = "light"


def render_sidebar():
    """Render the sidebar navigation"""

    with st.sidebar:
        st.title("⚡ PV Report")
        st.caption("Test Report Automation")

        st.divider()

        # User info (placeholder)
        st.write(f"👤 **User:** {st.session_state.username}")

        st.divider()

        # Navigation
        st.subheader("Navigation")

        pages = {
            "📊 Dashboard": "Dashboard",
            "📤 Upload Data": "Upload Data",
            "📝 Create Report": "Create Report",
            "📋 Review": "Review",
            "📦 Export": "Export"
        }

        for page_label, page_name in pages.items():
            if st.button(
                page_label,
                use_container_width=True,
                type="primary" if st.session_state.current_page == page_name else "secondary"
            ):
                st.session_state.current_page = page_name
                st.rerun()

        st.divider()

        # Session info
        st.subheader("Session Info")
        st.write(f"**Files Uploaded:** {len(st.session_state.uploaded_files)}")
        st.write(f"**Reports Created:** {len(st.session_state.reports)}")

        st.divider()

        # Settings
        with st.expander("⚙️ Settings"):
            st.write("**Theme:** Light (Default)")
            st.write("**Auto-save:** Enabled")

        # Logout placeholder
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.info("Logout functionality will be implemented in Phase 2")


def render_authentication():
    """Render authentication page (placeholder)"""

    st.title("🔐 Login")
    st.info("Authentication is disabled for Phase 1. Click below to continue.")

    if st.button("Continue to App", type="primary"):
        st.session_state.authenticated = True
        st.rerun()


def render_page():
    """Render the current page based on session state"""

    page = st.session_state.current_page

    if page == "Dashboard":
        render_dashboard()
    elif page == "Upload Data":
        render_upload_page()
    elif page == "Create Report":
        render_create_report_page()
    elif page == "Review":
        render_review_page()
    elif page == "Export":
        render_export_page()
    else:
        st.error(f"Unknown page: {page}")


def main():
    """Main application entry point"""

    # Initialize session state
    initialize_session_state()

    # Check authentication (placeholder)
    if not st.session_state.authenticated:
        render_authentication()
        return

    # Render sidebar
    render_sidebar()

    # Render main content
    render_page()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption("PV Test Report Automation - Phase 1 | © 2024")


if __name__ == "__main__":
    main()
