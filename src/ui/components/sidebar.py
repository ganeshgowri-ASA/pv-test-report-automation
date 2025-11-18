"""
Sidebar Navigation Component
Collapsible menu with icons, role-based visibility, and search functionality
"""
import streamlit as st
from typing import List, Dict, Optional


# Define menu structure with icons and role-based access
MENU_STRUCTURE = [
    {
        'name': 'Home',
        'icon': '🏠',
        'page': 'home',
        'roles': ['admin', 'engineer', 'reviewer', 'operator', 'viewer']
    },
    {
        'name': 'Test Management',
        'icon': '🔬',
        'page': None,
        'roles': ['admin', 'engineer', 'operator'],
        'children': [
            {'name': 'New Test', 'icon': '➕', 'page': 'new_test', 'roles': ['admin', 'engineer', 'operator']},
            {'name': 'Active Tests', 'icon': '▶️', 'page': 'active_tests', 'roles': ['admin', 'engineer', 'operator']},
            {'name': 'Completed Tests', 'icon': '✅', 'page': 'completed_tests', 'roles': ['admin', 'engineer', 'operator', 'viewer']},
            {'name': 'Test History', 'icon': '📊', 'page': 'test_history', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
        ]
    },
    {
        'name': 'Reports',
        'icon': '📄',
        'page': None,
        'roles': ['admin', 'engineer', 'reviewer', 'viewer'],
        'children': [
            {'name': 'Generate Report', 'icon': '📝', 'page': 'generate_report', 'roles': ['admin', 'engineer']},
            {'name': 'Draft Reports', 'icon': '📋', 'page': 'draft_reports', 'roles': ['admin', 'engineer', 'reviewer']},
            {'name': 'Published Reports', 'icon': '📑', 'page': 'published_reports', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
            {'name': 'Templates', 'icon': '📄', 'page': 'report_templates', 'roles': ['admin', 'engineer']},
        ]
    },
    {
        'name': 'Review Workflow',
        'icon': '✓',
        'page': None,
        'roles': ['admin', 'reviewer'],
        'children': [
            {'name': 'Pending Reviews', 'icon': '⏳', 'page': 'pending_reviews', 'roles': ['admin', 'reviewer']},
            {'name': 'My Reviews', 'icon': '👤', 'page': 'my_reviews', 'roles': ['admin', 'reviewer']},
            {'name': 'Review History', 'icon': '📚', 'page': 'review_history', 'roles': ['admin', 'reviewer']},
        ]
    },
    {
        'name': 'Standards',
        'icon': '📖',
        'page': None,
        'roles': ['admin', 'engineer', 'reviewer', 'viewer'],
        'children': [
            {'name': 'IEC 61215', 'icon': '📘', 'page': 'iec_61215', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
            {'name': 'IEC 61730', 'icon': '📘', 'page': 'iec_61730', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
            {'name': 'IEC 61853', 'icon': '📘', 'page': 'iec_61853', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
            {'name': 'ISO 17025', 'icon': '📗', 'page': 'iso_17025', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
            {'name': 'All Standards', 'icon': '📚', 'page': 'all_standards', 'roles': ['admin', 'engineer', 'reviewer', 'viewer']},
        ]
    },
    {
        'name': 'Equipment',
        'icon': '⚙️',
        'page': None,
        'roles': ['admin', 'engineer', 'operator'],
        'children': [
            {'name': 'Equipment List', 'icon': '📋', 'page': 'equipment_list', 'roles': ['admin', 'engineer', 'operator', 'viewer']},
            {'name': 'Calibration', 'icon': '🔧', 'page': 'calibration', 'roles': ['admin', 'engineer']},
            {'name': 'Maintenance', 'icon': '🛠️', 'page': 'maintenance', 'roles': ['admin', 'engineer', 'operator']},
        ]
    },
    {
        'name': 'Audit Trail',
        'icon': '📜',
        'page': 'audit_trail',
        'roles': ['admin', 'reviewer']
    },
    {
        'name': 'Analytics',
        'icon': '📊',
        'page': None,
        'roles': ['admin', 'engineer', 'reviewer'],
        'children': [
            {'name': 'Dashboard', 'icon': '📈', 'page': 'analytics_dashboard', 'roles': ['admin', 'engineer', 'reviewer']},
            {'name': 'Test Statistics', 'icon': '📊', 'page': 'test_statistics', 'roles': ['admin', 'engineer', 'reviewer']},
            {'name': 'Performance Metrics', 'icon': '📉', 'page': 'performance_metrics', 'roles': ['admin']},
        ]
    },
    {
        'name': 'Administration',
        'icon': '👥',
        'page': None,
        'roles': ['admin'],
        'children': [
            {'name': 'User Management', 'icon': '👤', 'page': 'user_management', 'roles': ['admin']},
            {'name': 'Role Management', 'icon': '🔐', 'page': 'role_management', 'roles': ['admin']},
            {'name': 'System Settings', 'icon': '⚙️', 'page': 'system_settings', 'roles': ['admin']},
            {'name': 'Backup & Restore', 'icon': '💾', 'page': 'backup_restore', 'roles': ['admin']},
        ]
    },
    {
        'name': 'Help',
        'icon': '❓',
        'page': None,
        'roles': ['admin', 'engineer', 'reviewer', 'operator', 'viewer'],
        'children': [
            {'name': 'Documentation', 'icon': '📖', 'page': 'documentation', 'roles': ['admin', 'engineer', 'reviewer', 'operator', 'viewer']},
            {'name': 'Training', 'icon': '🎓', 'page': 'training', 'roles': ['admin', 'engineer', 'reviewer', 'operator', 'viewer']},
            {'name': 'Support', 'icon': '💬', 'page': 'support', 'roles': ['admin', 'engineer', 'reviewer', 'operator', 'viewer']},
        ]
    },
]


def render_sidebar():
    """
    Renders the collapsible sidebar navigation with role-based menu items.
    Includes search functionality for quick navigation.
    """
    with st.sidebar:
        # Logo and title
        st.markdown("""
            <div style='text-align: center; padding: 1rem 0;'>
                <h2 style='color: #007bff; margin-bottom: 0;'>⚡ PV Lab</h2>
                <p style='color: #6c757d; font-size: 0.85rem; margin-top: 0;'>Test Report Automation</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Search box
        search_query = st.text_input("🔍 Search", placeholder="Search menu...", label_visibility="collapsed")

        st.markdown("---")

        # Get user role
        user_role = get_user_role()

        # Filter menu based on search
        if search_query:
            filtered_menu = search_menu_items(MENU_STRUCTURE, search_query, user_role)
            render_search_results(filtered_menu)
        else:
            # Render full menu
            render_menu_items(MENU_STRUCTURE, user_role)

        # Footer with system info
        st.markdown("---")
        render_sidebar_footer()


def get_user_role() -> str:
    """
    Gets the current user's role from session state.

    Returns:
        User role string (default: 'viewer')
    """
    if 'user' in st.session_state and st.session_state.user:
        return st.session_state.user.get('role', 'viewer').lower()
    return 'viewer'


def has_permission(item: Dict, user_role: str) -> bool:
    """
    Checks if user has permission to access a menu item.

    Args:
        item: Menu item dictionary
        user_role: User's role

    Returns:
        True if user has permission, False otherwise
    """
    if 'roles' not in item:
        return True
    return user_role in item['roles']


def render_menu_items(menu_items: List[Dict], user_role: str, level: int = 0):
    """
    Recursively renders menu items with proper indentation and role-based filtering.

    Args:
        menu_items: List of menu item dictionaries
        user_role: User's role for permission checking
        level: Indentation level (0 for top-level)
    """
    for item in menu_items:
        # Check permission
        if not has_permission(item, user_role):
            continue

        indent = "　" * level  # Use full-width space for indentation

        # Check if item has children
        if 'children' in item and item['children']:
            # Expandable section
            with st.expander(f"{indent}{item['icon']} {item['name']}", expanded=False):
                render_menu_items(item['children'], user_role, level + 1)
        else:
            # Single menu item
            if st.button(
                f"{indent}{item['icon']} {item['name']}",
                key=f"menu_{item.get('page', item['name'])}_{level}",
                use_container_width=True,
                type="primary" if st.session_state.get('current_page') == item.get('page') else "secondary"
            ):
                navigate_to_page(item.get('page', 'home'))


def navigate_to_page(page: str):
    """
    Navigates to the specified page.

    Args:
        page: Page identifier
    """
    st.session_state.current_page = page
    st.session_state.show_user_menu = False
    st.session_state.show_notifications = False
    st.rerun()


def search_menu_items(menu_items: List[Dict], query: str, user_role: str) -> List[Dict]:
    """
    Searches menu items recursively for matching items.

    Args:
        menu_items: List of menu item dictionaries
        query: Search query string
        user_role: User's role for permission checking

    Returns:
        List of matching menu items
    """
    results = []
    query_lower = query.lower()

    for item in menu_items:
        # Check permission first
        if not has_permission(item, user_role):
            continue

        # Check if name matches
        if query_lower in item['name'].lower():
            results.append(item)

        # Search in children
        if 'children' in item and item['children']:
            child_results = search_menu_items(item['children'], query, user_role)
            results.extend(child_results)

    return results


def render_search_results(results: List[Dict]):
    """
    Renders search results.

    Args:
        results: List of matching menu items
    """
    if not results:
        st.info("No matching menu items found.")
        return

    st.markdown("**Search Results:**")
    for item in results[:10]:  # Limit to 10 results
        if st.button(
            f"{item['icon']} {item['name']}",
            key=f"search_{item.get('page', item['name'])}",
            use_container_width=True
        ):
            navigate_to_page(item.get('page', 'home'))


def render_sidebar_footer():
    """
    Renders the sidebar footer with system information and quick links.
    """
    # System status indicator
    system_status = get_system_status()
    status_color = {
        'operational': '🟢',
        'warning': '🟡',
        'error': '🔴'
    }.get(system_status, '⚪')

    st.markdown(f"""
        <div style='text-align: center; font-size: 0.8rem; color: #6c757d;'>
            <p>System Status: {status_color}</p>
            <p>ISO 17025 Compliant</p>
            <p style='font-size: 0.7rem; margin-top: 0.5rem;'>v1.0.0 | © 2024</p>
        </div>
    """, unsafe_allow_html=True)

    # Quick actions
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📞 Support", use_container_width=True, key="sidebar_support"):
            st.session_state.current_page = 'support'
            st.rerun()

    with col2:
        if st.button("📖 Docs", use_container_width=True, key="sidebar_docs"):
            st.session_state.current_page = 'documentation'
            st.rerun()


@st.cache_data(ttl=60)
def get_system_status() -> str:
    """
    Gets the current system status.
    Cached for 60 seconds to reduce overhead.

    Returns:
        Status string: 'operational', 'warning', or 'error'
    """
    # TODO: Implement actual system health check
    # For now, return operational
    return 'operational'


def init_sidebar_state():
    """
    Initializes sidebar-related session state variables.
    """
    if 'sidebar_collapsed' not in st.session_state:
        st.session_state.sidebar_collapsed = False

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
