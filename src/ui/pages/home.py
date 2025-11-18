"""
Home Dashboard Page
Welcome screen with system overview, stats, activity feed, and quick actions
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List


def render_home_page():
    """
    Renders the main dashboard/home page with system overview and quick stats.
    ISO 17025 compliance: Displays audit trail summary and calibration status.
    """
    # Page header
    st.title("🏠 Dashboard")

    user = st.session_state.get('user', {})
    user_name = user.get('name', 'User')

    st.markdown(f"### Welcome back, {user_name}!")
    st.markdown(f"*Last login: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    st.markdown("---")

    # Quick stats row
    render_quick_stats()

    st.markdown("---")

    # Main content - two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        # Recent activity feed
        render_recent_activity()

        # Test statistics chart
        render_test_statistics()

    with col2:
        # Quick actions
        render_quick_actions()

        # System status
        render_system_status()

        # Upcoming tasks
        render_upcoming_tasks()

    # Bottom section - Full width
    st.markdown("---")

    # Standards compliance overview
    render_standards_compliance()


@st.cache_data(ttl=300)
def get_dashboard_stats() -> Dict:
    """
    Retrieves dashboard statistics.
    Cached for 5 minutes to improve performance.

    Returns:
        Dictionary with dashboard statistics
    """
    # TODO: Replace with actual database queries
    return {
        'active_tests': 12,
        'active_tests_change': '+3',
        'pending_reviews': 5,
        'pending_reviews_change': '+2',
        'reports_generated': 47,
        'reports_generated_change': '+8',
        'equipment_calibrated': 28,
        'equipment_calibrated_change': '98%',
        'tests_completed_this_week': 15,
        'tests_completed_this_month': 62,
        'avg_test_duration': 4.2,
        'review_turnaround_time': 2.3
    }


def render_quick_stats():
    """
    Renders quick statistics cards at the top of the dashboard.
    """
    stats = get_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🔬 Active Tests",
            value=stats['active_tests'],
            delta=stats['active_tests_change'],
            delta_color="normal"
        )

    with col2:
        st.metric(
            label="⏳ Pending Reviews",
            value=stats['pending_reviews'],
            delta=stats['pending_reviews_change'],
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="📄 Reports Generated",
            value=stats['reports_generated'],
            delta=stats['reports_generated_change'],
            delta_color="normal"
        )

    with col4:
        st.metric(
            label="⚙️ Equipment Status",
            value=f"{stats['equipment_calibrated']}/30",
            delta=stats['equipment_calibrated_change'],
            delta_color="off"
        )


def render_recent_activity():
    """
    Renders recent activity feed with filterable events.
    """
    st.subheader("📊 Recent Activity")

    # Activity filter
    activity_filter = st.multiselect(
        "Filter by type:",
        ["All", "Tests", "Reviews", "Reports", "Equipment", "Users"],
        default=["All"],
        key="activity_filter"
    )

    # Get recent activity
    activities = get_recent_activity()

    # Display activities
    for activity in activities[:10]:  # Show latest 10
        icon = get_activity_icon(activity['type'])
        timestamp = activity['timestamp'].strftime('%Y-%m-%d %H:%M')

        col1, col2 = st.columns([0.9, 0.1])

        with col1:
            st.markdown(f"""
                **{icon} {activity['title']}**
                {activity['description']}
                <small style='color: #6c757d;'>{timestamp} • {activity['user']}</small>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("→", key=f"activity_{activity['id']}", help="View details"):
                navigate_to_activity(activity)

        st.markdown("---")


@st.cache_data(ttl=60)
def get_recent_activity() -> List[Dict]:
    """
    Retrieves recent activity events.
    Cached for 60 seconds.

    Returns:
        List of activity dictionaries
    """
    # TODO: Replace with actual database queries
    now = datetime.now()

    return [
        {
            'id': 1,
            'type': 'test',
            'title': 'Test Completed',
            'description': 'IEC 61215-2024-001: Thermal Cycling completed successfully',
            'timestamp': now - timedelta(minutes=15),
            'user': 'Test Engineer'
        },
        {
            'id': 2,
            'type': 'review',
            'title': 'Review Submitted',
            'description': 'Technical review approved for report IEC-61730-2024-012',
            'timestamp': now - timedelta(hours=1),
            'user': 'Technical Reviewer'
        },
        {
            'id': 3,
            'type': 'report',
            'title': 'Report Published',
            'description': 'Final report published: IEC-61853-2024-005',
            'timestamp': now - timedelta(hours=2),
            'user': 'Administrator'
        },
        {
            'id': 4,
            'type': 'equipment',
            'title': 'Calibration Completed',
            'description': 'Multimeter DMM-2024-008 calibrated and verified',
            'timestamp': now - timedelta(hours=3),
            'user': 'Calibration Tech'
        },
        {
            'id': 5,
            'type': 'test',
            'title': 'Test Started',
            'description': 'IEC 62716-2024-003: Ammonia Corrosion Test initiated',
            'timestamp': now - timedelta(hours=4),
            'user': 'Lab Operator'
        },
        {
            'id': 6,
            'type': 'user',
            'title': 'User Login',
            'description': 'User "engineer" logged in from 192.168.1.100',
            'timestamp': now - timedelta(hours=5),
            'user': 'System'
        },
        {
            'id': 7,
            'type': 'review',
            'title': 'Review Requested',
            'description': 'Review requested for test IEC-61215-2024-002',
            'timestamp': now - timedelta(hours=6),
            'user': 'Test Engineer'
        },
        {
            'id': 8,
            'type': 'test',
            'title': 'Test Data Updated',
            'description': 'Measurements updated for IEC-60904-2024-007',
            'timestamp': now - timedelta(hours=8),
            'user': 'Lab Operator'
        }
    ]


def get_activity_icon(activity_type: str) -> str:
    """
    Returns icon for activity type.

    Args:
        activity_type: Type of activity

    Returns:
        Icon emoji
    """
    icons = {
        'test': '🔬',
        'review': '✓',
        'report': '📄',
        'equipment': '⚙️',
        'user': '👤',
        'system': 'ℹ️'
    }
    return icons.get(activity_type, '📌')


def navigate_to_activity(activity: Dict):
    """
    Navigates to the detail page for an activity.

    Args:
        activity: Activity dictionary
    """
    # TODO: Implement navigation based on activity type
    st.info(f"Navigate to {activity['type']} details")


def render_quick_actions():
    """
    Renders quick action buttons for common tasks.
    """
    st.subheader("⚡ Quick Actions")

    user_role = st.session_state.get('user', {}).get('role', 'viewer')

    # Role-based quick actions
    if user_role in ['admin', 'engineer', 'operator']:
        if st.button("➕ New Test", use_container_width=True, type="primary"):
            st.session_state.current_page = 'new_test'
            st.rerun()

    if user_role in ['admin', 'engineer']:
        if st.button("📝 Generate Report", use_container_width=True):
            st.session_state.current_page = 'generate_report'
            st.rerun()

    if user_role in ['admin', 'reviewer']:
        if st.button("✓ Review Queue", use_container_width=True):
            st.session_state.current_page = 'pending_reviews'
            st.rerun()

    # Common actions
    if st.button("📊 View All Tests", use_container_width=True):
        st.session_state.current_page = 'active_tests'
        st.rerun()

    if st.button("📄 View Reports", use_container_width=True):
        st.session_state.current_page = 'published_reports'
        st.rerun()

    if user_role in ['admin']:
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = 'user_management'
            st.rerun()


def render_system_status():
    """
    Renders system status widget with key indicators.
    """
    st.subheader("🖥️ System Status")

    # System metrics
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem;'>
            <p><strong>🟢 Operational</strong></p>
            <hr style='margin: 0.5rem 0;'>
            <p style='margin: 0.25rem 0;'>Database: <span style='color: green;'>●</span> Online</p>
            <p style='margin: 0.25rem 0;'>Storage: <span style='color: green;'>●</span> 78% Free</p>
            <p style='margin: 0.25rem 0;'>Backup: <span style='color: green;'>●</span> Today 03:00</p>
            <p style='margin: 0.25rem 0;'>API: <span style='color: green;'>●</span> Responsive</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # ISO 17025 Compliance Status
    st.markdown("""
        <div style='background-color: #e7f3ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #007bff;'>
            <p><strong>📋 ISO 17025 Status</strong></p>
            <hr style='margin: 0.5rem 0;'>
            <p style='margin: 0.25rem 0;'>Audit Trail: <span style='color: green;'>✓</span> Active</p>
            <p style='margin: 0.25rem 0;'>Traceability: <span style='color: green;'>✓</span> Verified</p>
            <p style='margin: 0.25rem 0;'>Calibrations: <span style='color: orange;'>!</span> 2 Due Soon</p>
        </div>
    """, unsafe_allow_html=True)


def render_upcoming_tasks():
    """
    Renders upcoming tasks and deadlines.
    """
    st.subheader("📅 Upcoming Tasks")

    tasks = get_upcoming_tasks()

    for task in tasks[:5]:  # Show top 5
        priority_color = {
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#28a745'
        }.get(task['priority'], '#6c757d')

        st.markdown(f"""
            <div style='padding: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid {priority_color}; background-color: #f8f9fa;'>
                <strong>{task['title']}</strong><br>
                <small style='color: #6c757d;'>Due: {task['due_date'].strftime('%Y-%m-%d')}</small>
            </div>
        """, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def get_upcoming_tasks() -> List[Dict]:
    """
    Retrieves upcoming tasks and deadlines.

    Returns:
        List of task dictionaries
    """
    # TODO: Replace with actual database queries
    now = datetime.now()

    return [
        {
            'id': 1,
            'title': 'Review IEC-61215-2024-001',
            'due_date': now + timedelta(days=1),
            'priority': 'high'
        },
        {
            'id': 2,
            'title': 'Complete UV Test Setup',
            'due_date': now + timedelta(days=2),
            'priority': 'medium'
        },
        {
            'id': 3,
            'title': 'Calibrate Temperature Sensors',
            'due_date': now + timedelta(days=5),
            'priority': 'high'
        },
        {
            'id': 4,
            'title': 'Submit Monthly Report',
            'due_date': now + timedelta(days=7),
            'priority': 'medium'
        },
        {
            'id': 5,
            'title': 'Equipment Maintenance Check',
            'due_date': now + timedelta(days=10),
            'priority': 'low'
        }
    ]


def render_test_statistics():
    """
    Renders test statistics chart showing test trends.
    """
    st.subheader("📈 Test Statistics (Last 30 Days)")

    # Generate sample data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = pd.DataFrame({
        'Date': dates,
        'Tests Completed': [3, 5, 2, 4, 6, 3, 4, 5, 7, 4, 3, 6, 5, 4, 3, 5, 6, 4, 5, 3, 4, 6, 5, 4, 3, 5, 6, 7, 4, 5],
        'Tests Started': [4, 6, 3, 5, 7, 4, 5, 6, 8, 5, 4, 7, 6, 5, 4, 6, 7, 5, 6, 4, 5, 7, 6, 5, 4, 6, 7, 8, 5, 6]
    })

    # Create chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Tests Completed'],
        mode='lines+markers',
        name='Completed',
        line=dict(color='#28a745', width=2),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Tests Started'],
        mode='lines+markers',
        name='Started',
        line=dict(color='#007bff', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Tests",
        hovermode='x unified',
        height=300,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_standards_compliance():
    """
    Renders standards compliance overview with progress indicators.
    """
    st.subheader("📖 Standards Compliance Overview")

    # Standards progress data
    standards = [
        {'name': 'IEC 61215', 'tests': 15, 'total': 20, 'color': '#007bff'},
        {'name': 'IEC 61730', 'tests': 8, 'total': 12, 'color': '#28a745'},
        {'name': 'IEC 61853', 'tests': 12, 'total': 15, 'color': '#ffc107'},
        {'name': 'IEC 62716', 'tests': 5, 'total': 8, 'color': '#dc3545'},
        {'name': 'ISO 17025', 'tests': 28, 'total': 30, 'color': '#6f42c1'}
    ]

    cols = st.columns(len(standards))

    for idx, standard in enumerate(standards):
        with cols[idx]:
            percentage = (standard['tests'] / standard['total']) * 100

            st.markdown(f"""
                <div style='text-align: center;'>
                    <h4 style='margin-bottom: 0.5rem;'>{standard['name']}</h4>
                    <div style='font-size: 2rem; font-weight: bold; color: {standard['color']};'>
                        {percentage:.0f}%
                    </div>
                    <p style='color: #6c757d; font-size: 0.9rem;'>
                        {standard['tests']}/{standard['total']} tests
                    </p>
                    <div style='background-color: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;'>
                        <div style='background-color: {standard['color']}; height: 100%; width: {percentage}%;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
