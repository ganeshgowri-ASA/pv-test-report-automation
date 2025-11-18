"""
Top Navigation Bar Component
Includes user info, notifications, dropdown menu, and breadcrumb navigation
"""
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional


def render_navbar():
    """
    Renders the top navigation bar with user info, notifications, and menu.
    Includes ISO 17025 compliance notifications and audit trail access.
    """
    if 'user' not in st.session_state or not st.session_state.user:
        return

    user = st.session_state.user

    # Create navbar container with custom styling
    st.markdown("""
        <style>
        .navbar {
            background-color: #f8f9fa;
            padding: 0.5rem 1rem;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        .navbar-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .notification-badge {
            background-color: #dc3545;
            color: white;
            border-radius: 50%;
            padding: 0.2rem 0.5rem;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .breadcrumb {
            color: #6c757d;
            font-size: 0.9rem;
        }
        .breadcrumb a {
            color: #007bff;
            text-decoration: none;
        }
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        .user-avatar {
            background-color: #007bff;
            color: white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Navbar layout
    col1, col2, col3 = st.columns([3, 4, 3])

    with col1:
        # Breadcrumb navigation
        breadcrumbs = get_breadcrumbs()
        st.markdown(f"<div class='breadcrumb'>{breadcrumbs}</div>", unsafe_allow_html=True)

    with col2:
        # System name and timestamp
        st.markdown(f"<div style='text-align: center; color: #6c757d;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)

    with col3:
        # User info and actions
        user_col1, user_col2, user_col3 = st.columns([1, 2, 1])

        with user_col1:
            # Notification bell
            notifications = get_user_notifications()
            notification_count = len(notifications)

            if notification_count > 0:
                if st.button(f"🔔 ({notification_count})", key="notifications_btn", help="View notifications"):
                    st.session_state.show_notifications = not st.session_state.get('show_notifications', False)
            else:
                st.button("🔔", key="notifications_btn_empty", help="No new notifications")

        with user_col2:
            # User menu dropdown
            user_name = user.get('name', user.get('username', 'User'))
            user_role = user.get('role', 'User')

            # Display user info
            st.markdown(f"""
                <div style='text-align: right; line-height: 1.2;'>
                    <div style='font-weight: bold; font-size: 0.9rem;'>{user_name}</div>
                    <div style='color: #6c757d; font-size: 0.75rem;'>{user_role}</div>
                </div>
            """, unsafe_allow_html=True)

        with user_col3:
            # User menu
            if st.button("⚙️", key="user_menu_btn", help="User menu"):
                st.session_state.show_user_menu = not st.session_state.get('show_user_menu', False)

    # Show notifications dropdown
    if st.session_state.get('show_notifications', False):
        render_notifications_dropdown(notifications)

    # Show user menu dropdown
    if st.session_state.get('show_user_menu', False):
        render_user_menu_dropdown(user)

    # Separator
    st.markdown("---")


def get_breadcrumbs() -> str:
    """
    Generates breadcrumb navigation based on current page.

    Returns:
        HTML string with breadcrumb navigation
    """
    current_page = st.session_state.get('current_page', 'Home')

    breadcrumbs_map = {
        'Home': ['Home'],
        'Tests': ['Home', 'Tests'],
        'Test Detail': ['Home', 'Tests', 'Test Detail'],
        'Reports': ['Home', 'Reports'],
        'Review': ['Home', 'Review'],
        'Settings': ['Home', 'Settings'],
        'Admin': ['Home', 'Admin'],
        'Audit Trail': ['Home', 'Audit Trail'],
    }

    crumbs = breadcrumbs_map.get(current_page, ['Home'])
    breadcrumb_html = ' / '.join([f"<a href='#'>{crumb}</a>" if i < len(crumbs) - 1 else crumb
                                   for i, crumb in enumerate(crumbs)])

    return breadcrumb_html


def get_user_notifications() -> List[Dict]:
    """
    Retrieves notifications for the current user.
    Includes ISO 17025 compliance alerts and review requests.

    Returns:
        List of notification dictionaries
    """
    # Initialize notifications in session state if not exists
    if 'notifications' not in st.session_state:
        st.session_state.notifications = [
            {
                'id': 1,
                'type': 'review',
                'title': 'Review Required',
                'message': 'Test report IEC-61215-2024-001 requires your review',
                'timestamp': datetime.now(),
                'read': False,
                'priority': 'high'
            },
            {
                'id': 2,
                'type': 'compliance',
                'title': 'Calibration Due',
                'message': 'Equipment CAL-2024-015 calibration due in 7 days',
                'timestamp': datetime.now(),
                'read': False,
                'priority': 'medium'
            },
            {
                'id': 3,
                'type': 'system',
                'title': 'System Update',
                'message': 'New ISO 17025 audit trail features available',
                'timestamp': datetime.now(),
                'read': False,
                'priority': 'low'
            }
        ]

    # Return unread notifications
    return [n for n in st.session_state.notifications if not n['read']]


def render_notifications_dropdown(notifications: List[Dict]):
    """
    Renders the notifications dropdown panel.

    Args:
        notifications: List of notification dictionaries
    """
    with st.expander("📬 Notifications", expanded=True):
        if not notifications:
            st.info("No new notifications")
        else:
            for notif in notifications[:5]:  # Show max 5 notifications
                priority_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(notif['priority'], '⚪')

                type_icon = {
                    'review': '📋',
                    'compliance': '⚠️',
                    'system': 'ℹ️'
                }.get(notif['type'], '📌')

                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    st.markdown(f"""
                        **{type_icon} {priority_icon} {notif['title']}**
                        {notif['message']}
                        <small style='color: #6c757d;'>{notif['timestamp'].strftime('%Y-%m-%d %H:%M')}</small>
                    """, unsafe_allow_html=True)

                with col2:
                    if st.button("✓", key=f"mark_read_{notif['id']}", help="Mark as read"):
                        mark_notification_read(notif['id'])
                        st.rerun()

                st.markdown("---")

            if len(notifications) > 5:
                st.info(f"+ {len(notifications) - 5} more notifications")

            if st.button("View All Notifications"):
                st.session_state.current_page = 'Notifications'
                st.rerun()


def render_user_menu_dropdown(user: Dict):
    """
    Renders the user menu dropdown with profile, settings, and logout options.

    Args:
        user: User information dictionary
    """
    with st.expander("👤 User Menu", expanded=True):
        st.markdown(f"**{user.get('name', user.get('username', 'User'))}**")
        st.markdown(f"*{user.get('email', 'user@example.com')}*")
        st.markdown(f"Role: {user.get('role', 'User')}")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.current_page = 'Profile'
                st.session_state.show_user_menu = False
                st.rerun()

            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = 'Settings'
                st.session_state.show_user_menu = False
                st.rerun()

        with col2:
            if st.button("📊 Activity", use_container_width=True):
                st.session_state.current_page = 'Activity'
                st.session_state.show_user_menu = False
                st.rerun()

            if st.button("🔒 Logout", use_container_width=True, type="primary"):
                logout_user()
                st.rerun()


def mark_notification_read(notification_id: int):
    """
    Marks a notification as read.

    Args:
        notification_id: ID of the notification to mark as read
    """
    if 'notifications' in st.session_state:
        for notif in st.session_state.notifications:
            if notif['id'] == notification_id:
                notif['read'] = True
                break


def logout_user():
    """
    Logs out the current user and clears session state.
    ISO 17025 audit trail: Records logout event.
    """
    # Record logout in audit trail
    if 'user' in st.session_state:
        user_id = st.session_state.user.get('id', 'unknown')
        # TODO: Log to audit trail database
        # audit_log.record_event('user_logout', user_id=user_id, timestamp=datetime.now())

    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.session_state.authenticated = False
    st.session_state.user = None
