"""Reusable UI Components Package.

This package provides reusable Streamlit components for:
- Data Tables: Paginated, sortable, filterable tables
- Charts: Interactive Plotly visualizations
- Forms: Form fields, validation, multi-step forms
- Navigation: Sidebar, breadcrumbs, menus
"""

# Data Tables
from .data_tables import (
    create_data_table,
    create_sortable_table,
    create_filterable_table,
    create_editable_table,
    create_selectable_table,
    create_summary_table,
    create_comparison_table,
)

# Charts
from .charts import (
    create_kpi_card,
    create_line_chart,
    create_bar_chart,
    create_pie_chart,
    create_status_chart,
    create_timeline_chart,
    create_performance_chart,
    create_gauge_chart,
    create_heatmap,
    create_scatter_plot,
    create_box_plot,
    create_histogram,
    create_area_chart,
    create_multi_axis_chart,
    create_waterfall_chart,
)

# Forms
from .forms import (
    create_form_field,
    create_file_uploader,
    create_validated_form,
    create_search_box,
    create_filter_group,
    create_pagination_controls,
    create_date_range_picker,
    create_confirmation_dialog,
    create_multi_step_form,
    create_dynamic_list,
)

# Navigation
from .navigation import (
    initialize_navigation_state,
    get_menu_items,
    render_sidebar,
    render_user_info,
    render_system_status,
    navigate_to,
    render_breadcrumbs,
    render_tabs,
    render_top_navigation,
    render_footer,
    render_back_button,
    create_page_header,
    create_context_menu,
    create_wizard_navigation,
    create_quick_links,
    render_secondary_navigation,
    create_dropdown_menu,
)


__all__ = [
    # Data Tables
    "create_data_table",
    "create_sortable_table",
    "create_filterable_table",
    "create_editable_table",
    "create_selectable_table",
    "create_summary_table",
    "create_comparison_table",
    # Charts
    "create_kpi_card",
    "create_line_chart",
    "create_bar_chart",
    "create_pie_chart",
    "create_status_chart",
    "create_timeline_chart",
    "create_performance_chart",
    "create_gauge_chart",
    "create_heatmap",
    "create_scatter_plot",
    "create_box_plot",
    "create_histogram",
    "create_area_chart",
    "create_multi_axis_chart",
    "create_waterfall_chart",
    # Forms
    "create_form_field",
    "create_file_uploader",
    "create_validated_form",
    "create_search_box",
    "create_filter_group",
    "create_pagination_controls",
    "create_date_range_picker",
    "create_confirmation_dialog",
    "create_multi_step_form",
    "create_dynamic_list",
    # Navigation
    "initialize_navigation_state",
    "get_menu_items",
    "render_sidebar",
    "render_user_info",
    "render_system_status",
    "navigate_to",
    "render_breadcrumbs",
    "render_tabs",
    "render_top_navigation",
    "render_footer",
    "render_back_button",
    "create_page_header",
    "create_context_menu",
    "create_wizard_navigation",
    "create_quick_links",
    "render_secondary_navigation",
    "create_dropdown_menu",
]
