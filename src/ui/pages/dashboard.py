"""
Dashboard page for PV Test Report Automation
Shows overview, statistics, and quick actions
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd


def render_dashboard():
    """Render the main dashboard page"""

    st.title("📊 PV Test Report Dashboard")

    # Initialize session state for reports if not exists
    if 'reports' not in st.session_state:
        st.session_state.reports = []

    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    # Statistics Cards
    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Reports",
            value=len(st.session_state.reports),
            delta=f"+{len([r for r in st.session_state.reports if r.get('created_today', False)])}"
                  if st.session_state.reports else None
        )

    with col2:
        st.metric(
            label="Uploaded Files",
            value=len(st.session_state.uploaded_files),
            delta=None
        )

    with col3:
        pending_reports = len([r for r in st.session_state.reports if r.get('status') == 'pending'])
        st.metric(
            label="Pending Reviews",
            value=pending_reports,
            delta=None
        )

    with col4:
        completed_reports = len([r for r in st.session_state.reports if r.get('status') == 'completed'])
        st.metric(
            label="Completed",
            value=completed_reports,
            delta=None
        )

    st.divider()

    # Quick Actions
    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Upload New Data", use_container_width=True, type="primary"):
            st.session_state.current_page = "Upload Data"
            st.rerun()

    with col2:
        if st.button("📝 Create New Report", use_container_width=True):
            st.session_state.current_page = "Create Report"
            st.rerun()

    with col3:
        if st.button("📋 Review Reports", use_container_width=True):
            st.session_state.current_page = "Review"
            st.rerun()

    st.divider()

    # Recent Reports Section
    st.subheader("📄 Recent Reports")

    if st.session_state.reports:
        # Create DataFrame from reports
        reports_df = pd.DataFrame(st.session_state.reports)

        # Display as table with styling
        st.dataframe(
            reports_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn("Report Name", width="medium"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "created_at": st.column_config.DatetimeColumn("Created", width="medium"),
                "files_count": st.column_config.NumberColumn("Files", width="small")
            }
        )
    else:
        st.info("No reports created yet. Get started by uploading data and creating your first report!")

    st.divider()

    # Activity Chart
    st.subheader("📈 Activity Overview")

    if st.session_state.reports:
        # Create sample activity data
        activity_data = create_activity_data(st.session_state.reports)

        fig = px.line(
            activity_data,
            x='date',
            y='count',
            title='Reports Created Over Time',
            markers=True
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Reports",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Activity chart will appear once you create reports.")

    # File Type Distribution
    if st.session_state.uploaded_files:
        st.subheader("📁 File Type Distribution")

        file_types = {}
        for file_info in st.session_state.uploaded_files:
            file_type = file_info.get('type', 'Unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1

        fig = go.Figure(data=[go.Pie(
            labels=list(file_types.keys()),
            values=list(file_types.values()),
            hole=.3
        )])

        fig.update_layout(title_text='Uploaded Files by Type')
        st.plotly_chart(fig, use_container_width=True)


def create_activity_data(reports):
    """Create activity data for visualization"""

    if not reports:
        return pd.DataFrame({'date': [], 'count': []})

    # Get dates from reports
    dates = []
    for report in reports:
        created_at = report.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                date = datetime.fromisoformat(created_at).date()
            else:
                date = created_at.date() if hasattr(created_at, 'date') else created_at
            dates.append(date)

    # Count reports per date
    if dates:
        date_counts = pd.Series(dates).value_counts().sort_index()
        activity_df = pd.DataFrame({
            'date': date_counts.index,
            'count': date_counts.values
        })
        return activity_df
    else:
        # Return last 7 days with zero counts
        last_week = [(datetime.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]
        return pd.DataFrame({
            'date': last_week,
            'count': [0] * 7
        })


if __name__ == "__main__":
    render_dashboard()
