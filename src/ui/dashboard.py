"""
Test Monitoring Dashboard - Streamlit Component.

Real-time test monitoring dashboard:
- Live test status
- Progress tracking
- Performance metrics
- Equipment status
- Alert notifications
"""

import streamlit as st
from datetime import datetime, timedelta
import random


def render_dashboard() -> None:
    """Render real-time test monitoring dashboard."""

    st.title("📊 Test Monitoring Dashboard")
    st.markdown("Real-time monitoring of PV module testing operations")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Active Tests",
            "12",
            delta="3",
            delta_color="normal",
        )

    with col2:
        st.metric(
            "Completed Today",
            "28",
            delta="8",
            delta_color="normal",
        )

    with col3:
        st.metric(
            "Pass Rate",
            "94.2%",
            delta="2.1%",
            delta_color="normal",
        )

    with col4:
        st.metric(
            "Equipment Status",
            "98%",
            delta="-1%",
            delta_color="inverse",
        )

    st.divider()

    # Active tests table
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🔄 Active Tests")

        # Sample test data
        test_data = {
            "Test ID": ["IEC61215-001", "IEC61730-002", "IEC61853-003", "IEC61701-004"],
            "Protocol": ["IEC 61215 MST", "IEC 61730 Safety", "IEC 61853 Perf", "IEC 61701 Salt"],
            "Progress": [45, 78, 23, 91],
            "Status": ["Running", "Running", "Running", "Completing"],
            "Started": ["2h ago", "4h ago", "1h ago", "6h ago"],
        }

        st.dataframe(test_data, use_container_width=True)

    with col2:
        st.subheader("⚙️ Equipment Status")

        equipment = {
            "Chamber-001": ("🟢", "Online"),
            "Chamber-002": ("🟢", "Online"),
            "Simulator-001": ("🟡", "Busy"),
            "Tester-001": ("🟢", "Online"),
        }

        for name, (status, state) in equipment.items():
            st.markdown(f"{status} **{name}**: {state}")

    st.divider()

    # Progress visualization
    st.subheader("📈 Test Progress")

    # Simulate progress bars for active tests
    for test_id, progress in zip(test_data["Test ID"], test_data["Progress"]):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.text(test_id)
        with col2:
            st.progress(progress / 100)

    # Recent alerts
    st.divider()
    st.subheader("🔔 Recent Alerts")

    alerts = [
        ("info", "Test IEC61215-001 reached 50% completion", "10 min ago"),
        ("success", "Calibration verified for Chamber-001", "25 min ago"),
        ("warning", "High temperature detected in test IEC61730-002", "1h ago"),
    ]

    for alert_type, message, time in alerts:
        if alert_type == "info":
            st.info(f"{message} • {time}")
        elif alert_type == "success":
            st.success(f"{message} • {time}")
        elif alert_type == "warning":
            st.warning(f"{message} • {time}")

    # Auto-refresh
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()


if __name__ == "__main__":
    render_dashboard()
