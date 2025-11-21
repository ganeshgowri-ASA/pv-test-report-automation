"""
Dashboard - Main overview and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def render():
    """Render the dashboard page"""
    st.title("🏠 Dashboard")
    st.markdown("### PV Test Automation System - Overview & Analytics")

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Total Tests",
            value="1,247",
            delta="+23 this week",
            delta_color="normal"
        )

    with col2:
        st.metric(
            label="✅ Completed Reports",
            value="1,198",
            delta="+18 this week",
            delta_color="normal"
        )

    with col3:
        st.metric(
            label="⏳ In Progress",
            value="32",
            delta="+5",
            delta_color="normal"
        )

    with col4:
        st.metric(
            label="✔️ Approval Rate",
            value="96.1%",
            delta="+1.2%",
            delta_color="normal"
        )

    st.markdown("---")

    # Two column layout
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 Test Activity Trend (Last 30 Days)")

        # Generate sample data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        test_data = pd.DataFrame({
            'Date': dates,
            'Tests Completed': [random.randint(30, 60) for _ in range(30)],
            'Reports Generated': [random.randint(25, 55) for _ in range(30)]
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=test_data['Date'],
            y=test_data['Tests Completed'],
            name='Tests Completed',
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=test_data['Date'],
            y=test_data['Reports Generated'],
            name='Reports Generated',
            mode='lines+markers',
            line=dict(color='#2ca02c', width=2)
        ))
        fig.update_layout(
            height=400,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🔬 Test Distribution")

        # Protocol distribution
        protocols = ['IEC 61215', 'IEC 61730', 'IEC 61853', 'IEC 62716', 'Other']
        counts = [450, 320, 280, 150, 47]

        fig_pie = px.pie(
            values=counts,
            names=protocols,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Recent activity section
    col_recent, col_alerts = st.columns(2)

    with col_recent:
        st.subheader("🕒 Recent Activity")

        recent_activities = [
            {"time": "5 min ago", "action": "Report approved", "user": "Dr. Sharma", "test_id": "PV-2024-1247"},
            {"time": "12 min ago", "action": "Test completed", "user": "Eng. Kumar", "test_id": "PV-2024-1246"},
            {"time": "28 min ago", "action": "Data uploaded", "user": "Tech. Patel", "test_id": "PV-2024-1245"},
            {"time": "1 hour ago", "action": "Review submitted", "user": "Dr. Sharma", "test_id": "PV-2024-1244"},
            {"time": "2 hours ago", "action": "Report generated", "user": "System", "test_id": "PV-2024-1243"},
        ]

        for activity in recent_activities:
            with st.container():
                st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.25rem 0; background-color: #f8f9fa; border-left: 3px solid #1f77b4; border-radius: 4px;">
                    <small style="color: #666;">{activity['time']}</small><br>
                    <strong>{activity['action']}</strong> by {activity['user']}<br>
                    <code>{activity['test_id']}</code>
                </div>
                """, unsafe_allow_html=True)

    with col_alerts:
        st.subheader("⚠️ Alerts & Notifications")

        st.warning("📅 **3 calibrations** due in next 7 days")
        st.info("📊 **2 reports** pending approval")
        st.success("✅ **Monthly audit** completed successfully")
        st.info("🔧 **Equipment EQ-045** maintenance scheduled for tomorrow")

    st.markdown("---")

    # Equipment status
    st.subheader("🔧 Equipment Status Overview")

    col_eq1, col_eq2, col_eq3, col_eq4 = st.columns(4)

    with col_eq1:
        st.markdown("""
        <div style="padding: 1rem; background-color: #d4edda; border-radius: 8px; text-align: center;">
            <h2 style="color: #155724; margin: 0;">28</h2>
            <p style="color: #155724; margin: 0;">✅ Operational</p>
        </div>
        """, unsafe_allow_html=True)

    with col_eq2:
        st.markdown("""
        <div style="padding: 1rem; background-color: #fff3cd; border-radius: 8px; text-align: center;">
            <h2 style="color: #856404; margin: 0;">3</h2>
            <p style="color: #856404; margin: 0;">⚠️ Calibration Due</p>
        </div>
        """, unsafe_allow_html=True)

    with col_eq3:
        st.markdown("""
        <div style="padding: 1rem; background-color: #cce5ff; border-radius: 8px; text-align: center;">
            <h2 style="color: #004085; margin: 0;">2</h2>
            <p style="color: #004085; margin: 0;">🔧 In Maintenance</p>
        </div>
        """, unsafe_allow_html=True)

    with col_eq4:
        st.markdown("""
        <div style="padding: 1rem; background-color: #f8d7da; border-radius: 8px; text-align: center;">
            <h2 style="color: #721c24; margin: 0;">1</h2>
            <p style="color: #721c24; margin: 0;">❌ Out of Service</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick actions
    st.subheader("⚡ Quick Actions")

    col_act1, col_act2, col_act3, col_act4 = st.columns(4)

    with col_act1:
        if st.button("🆕 New Test", use_container_width=True):
            st.info("Navigate to Protocol Selection to start a new test")

    with col_act2:
        if st.button("📤 Upload Data", use_container_width=True):
            st.info("Navigate to Data Upload to import test data")

    with col_act3:
        if st.button("📊 View Reports", use_container_width=True):
            st.info("Navigate to Report Generation to view all reports")

    with col_act4:
        if st.button("🔍 Audit Trail", use_container_width=True):
            st.info("Navigate to Audit Trail to view system logs")
