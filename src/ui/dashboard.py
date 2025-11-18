"""Main Dashboard for PV Test Report Automation System.

This module provides the main dashboard interface with KPIs, charts,
and system status overview.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .components.charts import (
    create_kpi_card,
    create_status_chart,
    create_timeline_chart,
    create_performance_chart,
)
from .components.data_tables import create_data_table
from .components.navigation import render_sidebar


def initialize_dashboard_state() -> None:
    """Initialize session state for dashboard."""
    if "dashboard_refresh" not in st.session_state:
        st.session_state.dashboard_refresh = datetime.now()
    if "dashboard_filter" not in st.session_state:
        st.session_state.dashboard_filter = "all"
    if "dashboard_timeframe" not in st.session_state:
        st.session_state.dashboard_timeframe = "7d"
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False


def get_kpi_metrics() -> Dict[str, Any]:
    """Fetch current KPI metrics.

    Returns:
        Dictionary containing KPI values and trends.
    """
    # TODO: Replace with actual data fetching logic
    return {
        "total_tests": {
            "value": 1247,
            "change": 12.5,
            "trend": "up",
            "period": "vs last week",
        },
        "passed_tests": {
            "value": 1186,
            "change": 8.3,
            "trend": "up",
            "period": "vs last week",
        },
        "active_equipment": {
            "value": 23,
            "change": 0,
            "trend": "stable",
            "period": "vs last week",
        },
        "avg_processing_time": {
            "value": 2.4,
            "unit": "min",
            "change": -15.2,
            "trend": "down",
            "period": "vs last week",
        },
        "reports_generated": {
            "value": 342,
            "change": 18.7,
            "trend": "up",
            "period": "vs last week",
        },
        "success_rate": {
            "value": 95.1,
            "unit": "%",
            "change": 2.1,
            "trend": "up",
            "period": "vs last week",
        },
    }


def get_test_status_data() -> pd.DataFrame:
    """Fetch test status data.

    Returns:
        DataFrame with test status information.
    """
    # TODO: Replace with actual data fetching logic
    data = {
        "status": ["Passed", "Failed", "In Progress", "Pending"],
        "count": [1186, 42, 15, 4],
        "percentage": [95.1, 3.4, 1.2, 0.3],
    }
    return pd.DataFrame(data)


def get_equipment_status() -> pd.DataFrame:
    """Fetch equipment status data.

    Returns:
        DataFrame with equipment status information.
    """
    # TODO: Replace with actual data fetching logic
    data = {
        "equipment_id": [f"PV-{i:03d}" for i in range(1, 11)],
        "type": ["Inverter", "Module", "Tracker", "Combiner"] * 3 + ["Inverter"] * 2,
        "status": ["Active", "Active", "Maintenance", "Active"] * 2 + ["Active", "Idle"],
        "last_test": [
            datetime.now() - timedelta(hours=i * 2) for i in range(10)
        ],
        "utilization": [98, 95, 0, 87, 92, 88, 76, 0, 94, 89],
    }
    df = pd.DataFrame(data)
    df["last_test"] = df["last_test"].dt.strftime("%Y-%m-%d %H:%M")
    return df


def get_recent_activity() -> List[Dict[str, Any]]:
    """Fetch recent activity data.

    Returns:
        List of recent activity events.
    """
    # TODO: Replace with actual data fetching logic
    activities = [
        {
            "timestamp": datetime.now() - timedelta(minutes=5),
            "type": "test_completed",
            "description": "IV Curve Test completed for PV-042",
            "user": "system",
            "status": "success",
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=12),
            "type": "report_generated",
            "description": "Monthly Performance Report generated",
            "user": "john.doe",
            "status": "success",
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=25),
            "type": "test_failed",
            "description": "Insulation Test failed for PV-038",
            "user": "system",
            "status": "error",
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=34),
            "type": "equipment_updated",
            "description": "PV-012 status changed to Maintenance",
            "user": "jane.smith",
            "status": "info",
        },
        {
            "timestamp": datetime.now() - timedelta(hours=1),
            "type": "test_started",
            "description": "Batch test started for 15 modules",
            "user": "system",
            "status": "info",
        },
    ]
    return activities


def render_kpi_section() -> None:
    """Render KPI metrics section."""
    st.subheader("Key Performance Indicators")

    kpis = get_kpi_metrics()

    # Create 3 columns for KPI cards
    col1, col2, col3 = st.columns(3)

    with col1:
        create_kpi_card(
            title="Total Tests",
            value=kpis["total_tests"]["value"],
            change=kpis["total_tests"]["change"],
            trend=kpis["total_tests"]["trend"],
            period=kpis["total_tests"]["period"],
        )
        create_kpi_card(
            title="Passed Tests",
            value=kpis["passed_tests"]["value"],
            change=kpis["passed_tests"]["change"],
            trend=kpis["passed_tests"]["trend"],
            period=kpis["passed_tests"]["period"],
        )

    with col2:
        create_kpi_card(
            title="Active Equipment",
            value=kpis["active_equipment"]["value"],
            change=kpis["active_equipment"]["change"],
            trend=kpis["active_equipment"]["trend"],
            period=kpis["active_equipment"]["period"],
        )
        create_kpi_card(
            title="Avg Processing Time",
            value=f"{kpis['avg_processing_time']['value']} {kpis['avg_processing_time']['unit']}",
            change=kpis["avg_processing_time"]["change"],
            trend=kpis["avg_processing_time"]["trend"],
            period=kpis["avg_processing_time"]["period"],
        )

    with col3:
        create_kpi_card(
            title="Reports Generated",
            value=kpis["reports_generated"]["value"],
            change=kpis["reports_generated"]["change"],
            trend=kpis["reports_generated"]["trend"],
            period=kpis["reports_generated"]["period"],
        )
        create_kpi_card(
            title="Success Rate",
            value=f"{kpis['success_rate']['value']}{kpis['success_rate']['unit']}",
            change=kpis["success_rate"]["change"],
            trend=kpis["success_rate"]["trend"],
            period=kpis["success_rate"]["period"],
        )


def render_test_status_overview() -> None:
    """Render test status overview section."""
    st.subheader("Test Status Overview")

    status_data = get_test_status_data()

    col1, col2 = st.columns([1, 2])

    with col1:
        # Status breakdown table
        st.dataframe(
            status_data,
            hide_index=True,
            use_container_width=True,
            column_config={
                "status": st.column_config.TextColumn("Status"),
                "count": st.column_config.NumberColumn("Count"),
                "percentage": st.column_config.NumberColumn(
                    "Percentage", format="%.1f%%"
                ),
            },
        )

    with col2:
        # Status pie chart
        fig = create_status_chart(status_data, "status", "count")
        st.plotly_chart(fig, use_container_width=True)


def render_equipment_status() -> None:
    """Render equipment status section."""
    st.subheader("Equipment Status")

    equipment_data = get_equipment_status()

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_status = st.multiselect(
            "Filter by Status",
            options=["Active", "Idle", "Maintenance"],
            default=["Active", "Idle", "Maintenance"],
        )
    with col2:
        if st.button("Refresh", key="refresh_equipment"):
            st.rerun()

    # Filter data
    filtered_data = equipment_data[equipment_data["status"].isin(filter_status)]

    # Display equipment table
    create_data_table(
        filtered_data,
        page_size=10,
        column_config={
            "equipment_id": st.column_config.TextColumn("Equipment ID"),
            "type": st.column_config.TextColumn("Type"),
            "status": st.column_config.TextColumn(
                "Status",
                help="Current equipment status",
            ),
            "last_test": st.column_config.TextColumn("Last Test"),
            "utilization": st.column_config.ProgressColumn(
                "Utilization",
                min_value=0,
                max_value=100,
                format="%d%%",
            ),
        },
    )


def render_recent_activity() -> None:
    """Render recent activity feed."""
    st.subheader("Recent Activity")

    activities = get_recent_activity()

    for activity in activities:
        # Determine icon and color based on status
        icon_map = {
            "success": "✓",
            "error": "✗",
            "info": "ℹ",
        }
        color_map = {
            "success": "green",
            "error": "red",
            "info": "blue",
        }

        icon = icon_map.get(activity["status"], "•")
        color = color_map.get(activity["status"], "gray")

        # Format timestamp
        time_str = activity["timestamp"].strftime("%H:%M:%S")

        # Create activity entry
        with st.container():
            col1, col2 = st.columns([1, 8])
            with col1:
                st.markdown(
                    f'<span style="color:{color};font-size:24px;">{icon}</span>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(f"**{time_str}** - {activity['description']}")
                st.caption(f"User: {activity['user']}")
            st.divider()


def render_quick_actions() -> None:
    """Render quick action buttons."""
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Upload Test Data", use_container_width=True):
            st.session_state.navigation = "upload"
            st.rerun()

    with col2:
        if st.button("Generate Report", use_container_width=True):
            st.session_state.navigation = "report_builder"
            st.rerun()

    with col3:
        if st.button("Review Reports", use_container_width=True):
            st.session_state.navigation = "review"
            st.rerun()

    with col4:
        if st.button("Export Data", use_container_width=True):
            st.session_state.navigation = "export"
            st.rerun()


def render_charts_section() -> None:
    """Render charts and visualizations section."""
    st.subheader("Analytics")

    # Time range selector
    timeframe = st.selectbox(
        "Time Range",
        options=["24h", "7d", "30d", "90d"],
        index=1,
        key="dashboard_timeframe_selector",
    )

    tab1, tab2, tab3 = st.tabs(["Test Trends", "Performance", "Equipment"])

    with tab1:
        # Test trends over time
        # TODO: Replace with actual data
        dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
        trend_data = pd.DataFrame({
            "date": dates,
            "passed": [30 + i * 2 for i in range(30)],
            "failed": [2 + (i % 5) for i in range(30)],
            "in_progress": [3 + (i % 3) for i in range(30)],
        })

        fig = create_timeline_chart(
            trend_data,
            x="date",
            y_columns=["passed", "failed", "in_progress"],
            title="Test Results Over Time",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Performance metrics
        # TODO: Replace with actual data
        perf_data = pd.DataFrame({
            "metric": ["Processing Time", "Success Rate", "Throughput"],
            "current": [2.4, 95.1, 48],
            "target": [3.0, 95.0, 45],
        })

        fig = create_performance_chart(perf_data)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Equipment utilization
        equipment_data = get_equipment_status()

        fig = px.bar(
            equipment_data,
            x="equipment_id",
            y="utilization",
            color="status",
            title="Equipment Utilization",
            labels={"utilization": "Utilization (%)", "equipment_id": "Equipment"},
        )
        st.plotly_chart(fig, use_container_width=True)


def render_dashboard() -> None:
    """Render the main dashboard page."""
    # Initialize state
    initialize_dashboard_state()

    # Page header
    st.title("PV Test Report Automation Dashboard")

    # Auto-refresh toggle
    col1, col2 = st.columns([6, 1])
    with col2:
        auto_refresh = st.toggle(
            "Auto-refresh",
            value=st.session_state.auto_refresh,
            key="auto_refresh_toggle",
        )
        st.session_state.auto_refresh = auto_refresh

    # Last updated timestamp
    st.caption(f"Last updated: {st.session_state.dashboard_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

    st.divider()

    # KPI Section
    render_kpi_section()

    st.divider()

    # Two-column layout for status and activity
    col1, col2 = st.columns([2, 1])

    with col1:
        render_test_status_overview()
        st.divider()
        render_equipment_status()

    with col2:
        render_recent_activity()

    st.divider()

    # Quick Actions
    render_quick_actions()

    st.divider()

    # Charts Section
    render_charts_section()

    # Auto-refresh logic
    if st.session_state.auto_refresh:
        import time
        time.sleep(30)
        st.session_state.dashboard_refresh = datetime.now()
        st.rerun()


if __name__ == "__main__":
    render_dashboard()
