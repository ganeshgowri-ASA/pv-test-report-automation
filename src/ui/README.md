# PV Test Report Automation - UI Components

Production-ready Streamlit UI components for the PV Test Report Automation System.

## Overview

This package provides a comprehensive user interface for managing PV test reports, including data upload, report building, review workflows, and export functionality.

## Components

### Main Interfaces

1. **dashboard.py** - Main Dashboard
   - KPI metrics display
   - Test status overview
   - Equipment status monitoring
   - Recent activity feed
   - Quick actions
   - Charts and visualizations

2. **upload_interface.py** - File Upload
   - Multi-file upload support
   - Drag-and-drop functionality
   - File validation
   - Progress tracking
   - Preview functionality
   - Batch processing

3. **report_builder.py** - Report Builder
   - Interactive report builder
   - Template selection
   - Section configuration
   - Data source mapping
   - Template customization
   - Real-time preview
   - Save/load configurations

4. **review_interface.py** - Report Review
   - Report review workflow
   - Commenting system
   - Approval/rejection workflow
   - Version comparison
   - Change tracking
   - Reviewer dashboard

5. **export_interface.py** - Export Manager
   - Format selection (PDF, Excel, Word, CSV, JSON, HTML)
   - Export options configuration
   - Batch export
   - Download management
   - Export history
   - Scheduled exports

### Reusable Components

Located in `components/` directory:

#### data_tables.py
- `create_data_table()` - Basic paginated table
- `create_sortable_table()` - Table with sorting
- `create_filterable_table()` - Table with filters
- `create_editable_table()` - Editable table
- `create_selectable_table()` - Table with row selection
- `create_summary_table()` - Summary statistics table
- `create_comparison_table()` - Side-by-side comparison

#### charts.py
- `create_kpi_card()` - KPI metric card
- `create_line_chart()` - Line chart
- `create_bar_chart()` - Bar chart
- `create_pie_chart()` - Pie/donut chart
- `create_status_chart()` - Status distribution chart
- `create_timeline_chart()` - Timeline visualization
- `create_performance_chart()` - Performance comparison
- `create_gauge_chart()` - Gauge/meter chart
- `create_heatmap()` - Heatmap
- `create_scatter_plot()` - Scatter plot
- `create_box_plot()` - Box plot
- `create_histogram()` - Histogram
- `create_area_chart()` - Area chart
- `create_multi_axis_chart()` - Multi-axis chart
- `create_waterfall_chart()` - Waterfall chart

#### forms.py
- `create_form_field()` - Generic form field
- `create_file_uploader()` - File upload widget
- `create_validated_form()` - Form with validation
- `create_search_box()` - Search input
- `create_filter_group()` - Filter controls
- `create_pagination_controls()` - Pagination widget
- `create_date_range_picker()` - Date range selector
- `create_confirmation_dialog()` - Confirmation dialog
- `create_multi_step_form()` - Wizard-style form
- `create_dynamic_list()` - Dynamic list editor

#### navigation.py
- `render_sidebar()` - Main sidebar navigation
- `render_breadcrumbs()` - Breadcrumb navigation
- `render_top_navigation()` - Top navigation bar
- `create_page_header()` - Page header component
- `create_context_menu()` - Context menu
- `create_wizard_navigation()` - Wizard navigation
- `create_quick_links()` - Quick links panel
- `render_secondary_navigation()` - Secondary menu
- `create_dropdown_menu()` - Dropdown menu

## Usage

### Running the Application

```bash
streamlit run src/ui/app.py
```

### Importing Components

```python
# Import main interfaces
from src.ui import (
    render_dashboard,
    render_upload_interface,
    render_report_builder,
    render_review_interface,
    render_export_interface,
)

# Import reusable components
from src.ui.components import (
    create_data_table,
    create_kpi_card,
    create_form_field,
    render_sidebar,
)
```

### Example: Using Data Table

```python
import pandas as pd
from src.ui.components import create_data_table

data = pd.DataFrame({
    "test_id": ["T001", "T002", "T003"],
    "status": ["Passed", "Failed", "Passed"],
    "value": [95.2, 88.1, 96.5],
})

create_data_table(
    data,
    page_size=10,
    column_config={
        "test_id": st.column_config.TextColumn("Test ID"),
        "status": st.column_config.TextColumn("Status"),
        "value": st.column_config.NumberColumn("Value", format="%.1f"),
    },
)
```

### Example: Creating Charts

```python
from src.ui.components import create_kpi_card, create_line_chart

# KPI Card
create_kpi_card(
    title="Total Tests",
    value=1247,
    change=12.5,
    trend="up",
    period="vs last week",
)

# Line Chart
fig = create_line_chart(
    data=test_data,
    x="date",
    y="count",
    title="Tests Over Time",
)
st.plotly_chart(fig)
```

## Features

### Session State Management
- Automatic state initialization
- Persistent navigation state
- Form data preservation
- User preferences storage

### Responsive Layouts
- Multi-column layouts
- Adaptive grid systems
- Mobile-friendly design
- Collapsible sections

### Error Handling
- Input validation
- Error messages
- Exception handling
- Graceful degradation

### Loading States
- Progress indicators
- Spinners for async operations
- Status messages
- Progress bars

## Testing

Run UI component tests:

```bash
# Run all UI tests
pytest src/ui/tests/

# Run specific test file
pytest src/ui/tests/test_dashboard.py

# Run with coverage
pytest src/ui/tests/ --cov=src.ui
```

## Best Practices

1. **State Management**
   - Always initialize session state
   - Use unique keys for widgets
   - Clean up unused state

2. **Performance**
   - Use caching where appropriate
   - Minimize reruns with callbacks
   - Lazy load large datasets

3. **User Experience**
   - Provide clear feedback
   - Show loading indicators
   - Validate inputs
   - Use consistent layouts

4. **Code Organization**
   - Keep components modular
   - Reuse common components
   - Follow naming conventions
   - Document complex logic

## Configuration

### Streamlit Configuration

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#007bff"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 200
enableCORS = false
```

## Dependencies

- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.17.0
- numpy >= 1.24.0

## Directory Structure

```
src/ui/
├── __init__.py
├── app.py                    # Main application
├── dashboard.py              # Dashboard interface
├── upload_interface.py       # Upload interface
├── report_builder.py         # Report builder
├── review_interface.py       # Review interface
├── export_interface.py       # Export interface
├── components/
│   ├── __init__.py
│   ├── data_tables.py       # Table components
│   ├── charts.py            # Chart components
│   ├── forms.py             # Form components
│   └── navigation.py        # Navigation components
├── tests/
│   ├── __init__.py
│   ├── test_dashboard.py
│   ├── test_components.py
│   └── test_interfaces.py
└── README.md
```

## Future Enhancements

- [ ] Dark mode support
- [ ] Internationalization (i18n)
- [ ] Advanced filtering
- [ ] Real-time updates with WebSocket
- [ ] Custom themes
- [ ] Export to additional formats
- [ ] Advanced analytics dashboards
- [ ] User role management
- [ ] Audit logging
- [ ] Mobile app version

## Support

For issues or questions, please refer to the main project documentation or create an issue in the project repository.
