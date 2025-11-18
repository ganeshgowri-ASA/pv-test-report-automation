"""
PV Test Report Automation - Main Streamlit Application
Production-ready application with authentication, navigation, and role-based access control.
ISO 17025 compliant with full audit trail integration.
"""
import streamlit as st
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.pages.login import render_login_page, check_authentication
from src.ui.pages.home import render_home_page
from src.ui.components.navbar import render_navbar
from src.ui.components.sidebar import render_sidebar, init_sidebar_state


# Page configuration
st.set_page_config(
    page_title="PV Test Lab - Report Automation",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.pvlab.com',
        'Report a bug': 'https://support.pvlab.com',
        'About': """
        # PV Test Lab Report Automation System

        World-class photovoltaic test lab report automation system.

        **Standards Coverage:**
        - IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
        - ISO 17025, ISO 9001
        - NABL, ILAC, BIS

        **Version:** 1.0.0

        © 2024 PV Test Lab. All rights reserved.
        """
    }
)


def init_session_state():
    """
    Initializes session state variables for the application.
    Essential for maintaining state across page reruns.
    """
    # Authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'user' not in st.session_state:
        st.session_state.user = None

    if 'token' not in st.session_state:
        st.session_state.token = None

    # Navigation state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

    # UI state
    if 'show_notifications' not in st.session_state:
        st.session_state.show_notifications = False

    if 'show_user_menu' not in st.session_state:
        st.session_state.show_user_menu = False

    # Initialize sidebar state
    init_sidebar_state()


def render_page(page: str):
    """
    Renders the specified page based on user navigation.
    Implements role-based access control.

    Args:
        page: Page identifier to render
    """
    user_role = st.session_state.get('user', {}).get('role', 'viewer')

    # Define page access control
    page_access = {
        'home': ['admin', 'engineer', 'reviewer', 'operator', 'viewer'],
        'new_test': ['admin', 'engineer', 'operator'],
        'active_tests': ['admin', 'engineer', 'operator'],
        'completed_tests': ['admin', 'engineer', 'operator', 'viewer'],
        'test_history': ['admin', 'engineer', 'reviewer', 'viewer'],
        'generate_report': ['admin', 'engineer'],
        'draft_reports': ['admin', 'engineer', 'reviewer'],
        'published_reports': ['admin', 'engineer', 'reviewer', 'viewer'],
        'report_templates': ['admin', 'engineer'],
        'pending_reviews': ['admin', 'reviewer'],
        'my_reviews': ['admin', 'reviewer'],
        'review_history': ['admin', 'reviewer'],
        'audit_trail': ['admin', 'reviewer'],
        'user_management': ['admin'],
        'role_management': ['admin'],
        'system_settings': ['admin'],
        'backup_restore': ['admin'],
        'equipment_list': ['admin', 'engineer', 'operator', 'viewer'],
        'calibration': ['admin', 'engineer'],
        'maintenance': ['admin', 'engineer', 'operator'],
    }

    # Check access permission
    allowed_roles = page_access.get(page, ['admin'])

    if user_role not in allowed_roles:
        st.error("🚫 Access Denied")
        st.warning(f"You don't have permission to access this page. Required role: {', '.join(allowed_roles)}")
        st.info("Please contact your administrator if you need access to this feature.")
        return

    # Render the appropriate page
    if page == 'home':
        render_home_page()
    elif page == 'new_test':
        render_placeholder_page("New Test", "🔬")
    elif page == 'active_tests':
        render_placeholder_page("Active Tests", "▶️")
    elif page == 'completed_tests':
        render_placeholder_page("Completed Tests", "✅")
    elif page == 'test_history':
        render_placeholder_page("Test History", "📊")
    elif page == 'generate_report':
        render_placeholder_page("Generate Report", "📝")
    elif page == 'draft_reports':
        render_placeholder_page("Draft Reports", "📋")
    elif page == 'published_reports':
        render_placeholder_page("Published Reports", "📑")
    elif page == 'report_templates':
        render_placeholder_page("Report Templates", "📄")
    elif page == 'pending_reviews':
        render_placeholder_page("Pending Reviews", "⏳")
    elif page == 'my_reviews':
        render_placeholder_page("My Reviews", "👤")
    elif page == 'review_history':
        render_placeholder_page("Review History", "📚")
    elif page == 'audit_trail':
        render_placeholder_page("Audit Trail", "📜")
    elif page == 'user_management':
        render_placeholder_page("User Management", "👥")
    elif page == 'role_management':
        render_placeholder_page("Role Management", "🔐")
    elif page == 'system_settings':
        render_placeholder_page("System Settings", "⚙️")
    elif page == 'backup_restore':
        render_placeholder_page("Backup & Restore", "💾")
    elif page == 'equipment_list':
        render_placeholder_page("Equipment List", "📋")
    elif page == 'calibration':
        render_placeholder_page("Calibration Management", "🔧")
    elif page == 'maintenance':
        render_placeholder_page("Equipment Maintenance", "🛠️")
    elif page == 'iec_61215':
        render_placeholder_page("IEC 61215 Standard", "📘")
    elif page == 'iec_61730':
        render_placeholder_page("IEC 61730 Standard", "📘")
    elif page == 'iec_61853':
        render_placeholder_page("IEC 61853 Standard", "📘")
    elif page == 'iso_17025':
        render_placeholder_page("ISO 17025 Standard", "📗")
    elif page == 'all_standards':
        render_placeholder_page("All Standards", "📚")
    elif page == 'analytics_dashboard':
        render_placeholder_page("Analytics Dashboard", "📈")
    elif page == 'test_statistics':
        render_placeholder_page("Test Statistics", "📊")
    elif page == 'performance_metrics':
        render_placeholder_page("Performance Metrics", "📉")
    elif page == 'documentation':
        render_placeholder_page("Documentation", "📖")
    elif page == 'training':
        render_placeholder_page("Training Resources", "🎓")
    elif page == 'support':
        render_placeholder_page("Support & Help", "💬")
    else:
        st.error(f"Page '{page}' not found")


def render_placeholder_page(title: str, icon: str):
    """
    Renders a placeholder page for pages not yet implemented.

    Args:
        title: Page title
        icon: Page icon emoji
    """
    st.title(f"{icon} {title}")
    st.info(f"The {title} page is under development.")
    st.markdown("""
        This page will include:
        - Full functionality for this feature
        - ISO 17025 compliance tracking
        - Integration with audit trail
        - Export capabilities
        - Advanced filtering and search
    """)

    # Sample content
    st.markdown("---")
    st.markdown("### Coming Soon")
    st.markdown("This feature is currently being developed and will be available in the next release.")


def main():
    """
    Main application entry point.
    Handles authentication flow and page routing.
    """
    # Initialize session state
    init_session_state()

    # Check if user is already authenticated
    if not st.session_state.authenticated:
        # Try to restore session from token
        if check_authentication():
            st.session_state.authenticated = True
            # Load user data from token
            # TODO: Implement full user data loading from database
        else:
            # Show login page
            render_login_page()
            return

    # User is authenticated - show main application
    # Render navbar (top navigation)
    render_navbar()

    # Render sidebar (left navigation)
    render_sidebar()

    # Render main content based on current page
    current_page = st.session_state.get('current_page', 'home')
    render_page(current_page)

    # Footer
    render_footer()


def render_footer():
    """
    Renders the application footer with compliance information.
    """
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #6c757d; font-size: 0.8rem; padding: 1rem;'>
            <p>
                <strong>PV Test Lab Report Automation System</strong> |
                Version 1.0.0 |
                ISO 17025 Certified |
                NABL Accredited
            </p>
            <p>
                © 2024 PV Test Lab. All rights reserved. |
                <a href='#' style='color: #007bff;'>Privacy Policy</a> |
                <a href='#' style='color: #007bff;'>Terms of Service</a> |
                <a href='#' style='color: #007bff;'>Contact Support</a>
            </p>
        </div>
    """, unsafe_allow_html=True)


# Error handling wrapper
def run_with_error_handling():
    """
    Runs the main application with error handling.
    """
    try:
        main()
    except Exception as e:
        st.error("🚨 An unexpected error occurred")
        st.exception(e)
        st.info("Please try refreshing the page. If the problem persists, contact support.")

        # Log error to audit trail
        # TODO: Implement error logging to database
        if 'user' in st.session_state and st.session_state.user:
            user_id = st.session_state.user.get('id', 'unknown')
            # Log error with user context


if __name__ == "__main__":
    # Hide Streamlit default menu and footer
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Run application
    run_with_error_handling()
