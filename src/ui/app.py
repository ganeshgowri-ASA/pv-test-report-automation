"""Main Streamlit Application Entry Point.

This is the main application file that orchestrates all UI components
and handles page routing.
"""

import streamlit as st
from typing import Dict, Callable

from .dashboard import render_dashboard
from .upload_interface import render_upload_interface
from .report_builder import render_report_builder
from .review_interface import render_review_interface
from .export_interface import render_export_interface
from .components.navigation import render_sidebar


# Page configuration
st.set_page_config(
    page_title="PV Test Report Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_page_routes() -> Dict[str, Callable]:
    """Get mapping of page IDs to render functions.

    Returns:
        Dictionary mapping page IDs to render functions.
    """
    return {
        "dashboard": render_dashboard,
        "upload": render_upload_interface,
        "report_builder": render_report_builder,
        "review": render_review_interface,
        "export": render_export_interface,
        "settings": render_settings_page,
    }


def render_settings_page() -> None:
    """Render settings page."""
    st.title("Settings")
    st.write("Settings page coming soon...")

    st.subheader("General Settings")
    st.checkbox("Enable auto-refresh", value=True)
    st.checkbox("Enable notifications", value=True)

    st.subheader("Display Settings")
    st.selectbox("Theme", options=["Light", "Dark", "Auto"])
    st.number_input("Refresh interval (seconds)", min_value=10, value=30)

    st.subheader("Data Settings")
    st.number_input("Max upload size (MB)", min_value=1, value=50)
    st.number_input("Page size", min_value=5, value=10)


def apply_custom_css() -> None:
    """Apply custom CSS styling."""
    st.markdown(
        """
        <style>
        /* Custom styling for the app */
        .stButton>button {
            border-radius: 4px;
        }

        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }

        div[data-testid="stExpander"] {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }

        /* Improve table styling */
        .dataframe {
            font-size: 14px;
        }

        /* Card styling */
        .element-container {
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_app_state() -> None:
    """Initialize application-wide session state."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user = {
            "name": "John Doe",
            "role": "Administrator",
            "email": "john.doe@example.com",
        }


def main() -> None:
    """Main application entry point."""
    # Initialize app state
    initialize_app_state()

    # Apply custom styling
    apply_custom_css()

    # Render sidebar and get current page
    current_page = render_sidebar()

    # Get page routes
    routes = get_page_routes()

    # Render current page
    if current_page in routes:
        try:
            routes[current_page]()
        except Exception as e:
            st.error(f"Error rendering page: {str(e)}")
            st.exception(e)
    else:
        st.error(f"Page '{current_page}' not found")


if __name__ == "__main__":
    main()
