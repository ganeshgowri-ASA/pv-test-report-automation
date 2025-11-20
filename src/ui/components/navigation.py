"""Navigation Components.

This module provides reusable navigation components including sidebar,
menus, breadcrumbs, and page routing.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable


def initialize_navigation_state() -> None:
    """Initialize navigation state."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    if "navigation_history" not in st.session_state:
        st.session_state.navigation_history = []
    if "sidebar_expanded" not in st.session_state:
        st.session_state.sidebar_expanded = True


def get_menu_items() -> List[Dict[str, Any]]:
    """Get main menu items.

    Returns:
        List of menu item configurations.
    """
    return [
        {
            "id": "dashboard",
            "label": "Dashboard",
            "icon": "📊",
            "description": "System overview and KPIs",
        },
        {
            "id": "upload",
            "label": "Upload Data",
            "icon": "📤",
            "description": "Upload test data files",
        },
        {
            "id": "report_builder",
            "label": "Build Report",
            "icon": "📝",
            "description": "Create custom reports",
        },
        {
            "id": "review",
            "label": "Review Reports",
            "icon": "✓",
            "description": "Review and approve reports",
        },
        {
            "id": "export",
            "label": "Export",
            "icon": "📥",
            "description": "Export reports and data",
        },
        {
            "id": "settings",
            "label": "Settings",
            "icon": "⚙",
            "description": "System settings",
        },
    ]


def render_sidebar() -> str:
    """Render the sidebar navigation.

    Returns:
        Selected page ID.
    """
    initialize_navigation_state()

    with st.sidebar:
        # Logo/Title
        st.title("PV Test Automation")
        st.caption("Report Management System")

        st.divider()

        # Main menu
        menu_items = get_menu_items()

        selected_page = st.session_state.current_page

        for item in menu_items:
            # Highlight current page
            is_current = item["id"] == selected_page

            if st.button(
                f"{item['icon']} {item['label']}",
                key=f"nav_{item['id']}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                navigate_to(item["id"])

        st.divider()

        # User info
        render_user_info()

        # System status
        st.divider()
        render_system_status()

    return st.session_state.current_page


def render_user_info() -> None:
    """Render user information in sidebar."""
    st.write("**User:**")
    st.caption("John Doe")
    st.caption("Administrator")

    with st.expander("Account"):
        if st.button("Profile", use_container_width=True):
            st.info("Profile page coming soon")

        if st.button("Logout", use_container_width=True):
            st.info("Logout functionality coming soon")


def render_system_status() -> None:
    """Render system status in sidebar."""
    st.write("**System Status:**")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.caption("Database")
        st.caption("API Server")
        st.caption("Storage")

    with col2:
        st.success("●")
        st.success("●")
        st.warning("●")


def navigate_to(page_id: str) -> None:
    """Navigate to a specific page.

    Args:
        page_id: Page identifier.
    """
    # Add to history
    if st.session_state.current_page != page_id:
        st.session_state.navigation_history.append(st.session_state.current_page)

    st.session_state.current_page = page_id
    st.rerun()


def render_breadcrumbs(items: List[str]) -> None:
    """Render breadcrumb navigation.

    Args:
        items: List of breadcrumb items.
    """
    breadcrumb_html = " › ".join(items)
    st.caption(breadcrumb_html)


def render_tabs(
    tabs: List[str],
    key: Optional[str] = None,
) -> str:
    """Render tab navigation.

    Args:
        tabs: List of tab labels.
        key: Unique key for tabs.

    Returns:
        Selected tab.
    """
    selected_tab = st.tabs(tabs)
    return selected_tab


def render_top_navigation() -> None:
    """Render top navigation bar."""
    col1, col2, col3 = st.columns([2, 3, 1])

    with col1:
        st.title("PV Test Report Automation")

    with col2:
        # Quick search
        search_query = st.text_input(
            "",
            placeholder="Search reports, tests, equipment...",
            key="global_search",
            label_visibility="collapsed",
        )

        if search_query:
            st.info(f"Searching for: {search_query}")

    with col3:
        # Notifications
        if st.button("🔔 Notifications"):
            show_notifications()


def show_notifications() -> None:
    """Show notification panel."""
    st.sidebar.subheader("Notifications")

    notifications = [
        {
            "title": "Report Approved",
            "message": "RPT-0042 has been approved",
            "time": "2 hours ago",
            "type": "success",
        },
        {
            "title": "Test Failed",
            "message": "Insulation test failed for PV-038",
            "time": "5 hours ago",
            "type": "error",
        },
        {
            "title": "New Data Uploaded",
            "message": "15 new test files uploaded",
            "time": "1 day ago",
            "type": "info",
        },
    ]

    for notif in notifications:
        with st.sidebar.expander(f"{notif['title']} - {notif['time']}"):
            st.write(notif["message"])


def render_footer() -> None:
    """Render page footer."""
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("© 2024 PV Test Automation")

    with col2:
        st.caption("Version 0.1.0")

    with col3:
        st.caption("[Documentation](#) | [Support](#)")


def render_back_button(callback: Optional[Callable] = None) -> None:
    """Render a back button.

    Args:
        callback: Optional callback function when clicked.
    """
    if st.button("← Back"):
        if callback:
            callback()
        elif st.session_state.navigation_history:
            previous_page = st.session_state.navigation_history.pop()
            st.session_state.current_page = previous_page
            st.rerun()


def create_page_header(
    title: str,
    subtitle: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Create a page header with title and actions.

    Args:
        title: Page title.
        subtitle: Optional subtitle.
        actions: Optional list of action button configurations.
    """
    if actions:
        cols = st.columns([3, 1])

        with cols[0]:
            st.title(title)
            if subtitle:
                st.caption(subtitle)

        with cols[1]:
            for action in actions:
                if st.button(
                    action["label"],
                    key=action.get("key"),
                    type=action.get("type", "secondary"),
                ):
                    if "callback" in action:
                        action["callback"]()
    else:
        st.title(title)
        if subtitle:
            st.caption(subtitle)


def create_context_menu(
    items: List[Dict[str, Any]],
    trigger_label: str = "Actions",
    key: Optional[str] = None,
) -> Optional[str]:
    """Create a context menu.

    Args:
        items: List of menu item configurations.
        trigger_label: Label for the trigger button.
        key: Unique key.

    Returns:
        Selected action ID or None.
    """
    with st.popover(trigger_label):
        for item in items:
            if st.button(
                f"{item.get('icon', '')} {item['label']}",
                key=f"{key}_{item['id']}" if key else None,
                use_container_width=True,
            ):
                return item["id"]

    return None


def create_wizard_navigation(
    steps: List[str],
    current_step: int,
    on_previous: Optional[Callable] = None,
    on_next: Optional[Callable] = None,
    on_finish: Optional[Callable] = None,
) -> None:
    """Create wizard-style navigation.

    Args:
        steps: List of step labels.
        current_step: Current step index (0-based).
        on_previous: Callback for previous button.
        on_next: Callback for next button.
        on_finish: Callback for finish button.
    """
    # Step indicator
    st.write("**Steps:**")

    cols = st.columns(len(steps))

    for idx, step in enumerate(steps):
        with cols[idx]:
            if idx < current_step:
                st.success(f"✓ {step}")
            elif idx == current_step:
                st.info(f"→ {step}")
            else:
                st.caption(step)

    st.divider()

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_step > 0:
            if st.button("← Previous"):
                if on_previous:
                    on_previous()

    with col3:
        if current_step < len(steps) - 1:
            if st.button("Next →"):
                if on_next:
                    on_next()
        else:
            if st.button("Finish", type="primary"):
                if on_finish:
                    on_finish()


def create_quick_links(
    links: List[Dict[str, Any]],
    title: str = "Quick Links",
) -> None:
    """Create a quick links panel.

    Args:
        links: List of link configurations.
        title: Panel title.
    """
    st.subheader(title)

    cols = st.columns(min(len(links), 3))

    for idx, link in enumerate(links):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"**{link.get('icon', '')} {link['label']}**")
                st.caption(link.get('description', ''))

                if st.button("Go", key=f"quick_link_{link['id']}", use_container_width=True):
                    if "callback" in link:
                        link["callback"]()
                    elif "page" in link:
                        navigate_to(link["page"])


def render_secondary_navigation(
    items: List[str],
    key: Optional[str] = None,
) -> str:
    """Render secondary navigation menu.

    Args:
        items: List of navigation items.
        key: Unique key.

    Returns:
        Selected item.
    """
    cols = st.columns(len(items))

    # Initialize selected item
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = items[0]

    selected = st.session_state[f"{key}_selected"]

    for idx, item in enumerate(items):
        with cols[idx]:
            if st.button(
                item,
                key=f"{key}_{idx}" if key else None,
                use_container_width=True,
                type="primary" if item == selected else "secondary",
            ):
                st.session_state[f"{key}_selected"] = item
                selected = item

    return selected


def create_dropdown_menu(
    label: str,
    items: List[Dict[str, Any]],
    key: Optional[str] = None,
) -> Optional[str]:
    """Create a dropdown menu.

    Args:
        label: Menu label.
        items: List of menu item configurations.
        key: Unique key.

    Returns:
        Selected item ID or None.
    """
    item_labels = [item["label"] for item in items]

    selected_label = st.selectbox(
        label,
        options=item_labels,
        key=key,
    )

    # Find selected item
    for item in items:
        if item["label"] == selected_label:
            if "callback" in item:
                item["callback"]()
            return item.get("id")

    return None
