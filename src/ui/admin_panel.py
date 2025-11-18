"""
Admin Panel UI - Streamlit Component.

System administration interface:
- User management
- System configuration
- Audit logs
- Database management
- API key management
"""

import streamlit as st
from datetime import datetime


def render_admin_panel() -> None:
    """Render system administration panel."""

    st.title("⚙️ System Administration")

    # Check admin access (simplified)
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin authentication required")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("🔓 Login", type="primary", use_container_width=True):
                if username == "admin" and password == "admin":  # Simplified auth
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return

    # Admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Users",
        "🔑 API Keys",
        "⚙️ Configuration",
        "📊 System Status",
        "📜 Audit Logs"
    ])

    with tab1:
        st.subheader("User Management")

        # User list
        users = [
            {"username": "john.doe", "email": "john@example.com", "role": "Engineer", "status": "Active"},
            {"username": "jane.smith", "email": "jane@example.com", "role": "Reviewer", "status": "Active"},
            {"username": "admin", "email": "admin@example.com", "role": "Admin", "status": "Active"},
        ]

        st.dataframe(users, use_container_width=True)

        st.divider()

        # Add new user
        with st.expander("➕ Add New User"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
            with col2:
                new_role = st.selectbox("Role", ["Engineer", "Reviewer", "QA", "Admin"])
                new_password = st.text_input("Password", type="password")

            if st.button("Create User", type="primary"):
                st.success(f"User '{new_username}' created successfully!")

    with tab2:
        st.subheader("API Key Management")

        # API keys
        api_keys = [
            {"provider": "Claude", "status": "Active", "last_used": "2 hours ago", "usage": 1234},
            {"provider": "OpenAI", "status": "Active", "last_used": "5 hours ago", "usage": 567},
            {"provider": "Gemini", "status": "Inactive", "last_used": "Never", "usage": 0},
        ]

        for key in api_keys:
            with st.expander(f"🔑 {key['provider']} API Key"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", key["status"])
                with col2:
                    st.metric("Last Used", key["last_used"])
                with col3:
                    st.metric("Usage Count", key["usage"])

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🔄 Rotate", key=f"rotate_{key['provider']}"):
                        st.success("Key rotated!")
                with col2:
                    if st.button(f"❌ Revoke", key=f"revoke_{key['provider']}"):
                        st.warning("Key revoked!")

    with tab3:
        st.subheader("System Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Database Settings**")
            db_host = st.text_input("Database Host", value="localhost")
            db_port = st.number_input("Database Port", value=5432)
            db_name = st.text_input("Database Name", value="pv_test_automation")

        with col2:
            st.markdown("**Application Settings**")
            max_upload_size = st.number_input("Max Upload Size (MB)", value=100)
            session_timeout = st.number_input("Session Timeout (minutes)", value=30)
            enable_metrics = st.checkbox("Enable Prometheus Metrics", value=True)

        st.divider()

        if st.button("💾 Save Configuration", type="primary"):
            st.success("Configuration saved successfully!")

    with tab4:
        st.subheader("System Status")

        # System metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Database", "Online", delta="99.9%")
        with col2:
            st.metric("API", "Healthy", delta="100%")
        with col3:
            st.metric("Storage", "72%", delta="5%")
        with col4:
            st.metric("Memory", "4.2GB", delta="0.3GB")

        st.divider()

        # Service status
        services = [
            {"name": "PostgreSQL", "status": "🟢 Running", "uptime": "45 days"},
            {"name": "Redis", "status": "🟢 Running", "uptime": "45 days"},
            {"name": "API Server", "status": "🟢 Running", "uptime": "12 days"},
            {"name": "Background Tasks", "status": "🟢 Running", "uptime": "12 days"},
        ]

        st.dataframe(services, use_container_width=True)

    with tab5:
        st.subheader("Audit Logs")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            log_type = st.selectbox("Type", ["All", "Login", "Export", "Review", "System"])
        with col2:
            log_user = st.selectbox("User", ["All", "john.doe", "jane.smith", "admin"])
        with col3:
            log_date = st.date_input("Date")

        # Sample logs
        logs = [
            {"timestamp": "2024-01-15 14:23:45", "user": "john.doe", "action": "Report Exported", "details": "IEC61215-001.pdf"},
            {"timestamp": "2024-01-15 13:15:22", "user": "jane.smith", "action": "Review Approved", "details": "IEC61730-002"},
            {"timestamp": "2024-01-15 12:05:11", "user": "admin", "action": "User Created", "details": "new.user@example.com"},
            {"timestamp": "2024-01-15 11:45:33", "user": "john.doe", "action": "Login", "details": "Successful"},
        ]

        st.dataframe(logs, use_container_width=True)

        if st.button("⬇️ Export Audit Logs"):
            st.success("Audit logs exported to audit_log.csv")


if __name__ == "__main__":
    render_admin_panel()
