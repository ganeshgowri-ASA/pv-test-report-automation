"""
Review page for PV Test Report Automation
Placeholder for Phase 2
"""

import streamlit as st


def render_review_page():
    """Render the review page"""

    st.title("📋 Review Reports")

    st.info("🚧 This feature will be implemented in Phase 2")

    st.markdown("""
    ### Coming Soon:
    - List of generated reports
    - Report preview
    - Edit and modify reports
    - Approval workflow
    - Comments and annotations
    """)

    # Show reports count
    if 'reports' in st.session_state:
        reports_count = len(st.session_state.reports)
        if reports_count > 0:
            st.success(f"✅ {reports_count} report(s) available for review")
        else:
            st.info("No reports created yet.")

    if st.button("← Back to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()


if __name__ == "__main__":
    render_review_page()
