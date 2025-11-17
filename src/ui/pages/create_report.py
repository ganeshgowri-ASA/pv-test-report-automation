"""
Create Report page for PV Test Report Automation
Placeholder for Phase 2
"""

import streamlit as st


def render_create_report_page():
    """Render the create report page"""

    st.title("📝 Create Report")

    st.info("🚧 This feature will be implemented in Phase 2")

    st.markdown("""
    ### Coming Soon:
    - Report template selection
    - Data field mapping
    - Custom report sections
    - Report generation preview
    """)

    # Show uploaded files count
    if 'uploaded_files' in st.session_state:
        files_count = len(st.session_state.uploaded_files)
        if files_count > 0:
            st.success(f"✅ {files_count} file(s) ready for report creation")
        else:
            st.warning("⚠️ No files uploaded yet. Please upload files first.")

    if st.button("← Back to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()


if __name__ == "__main__":
    render_create_report_page()
