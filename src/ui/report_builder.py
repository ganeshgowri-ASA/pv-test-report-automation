"""Report Builder Interface for PV Test Report Automation System.

This module provides an interactive interface for building custom reports
with section selection, data mapping, and real-time preview.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from .components.forms import create_form_field
from .components.data_tables import create_data_table


def initialize_report_builder_state() -> None:
    """Initialize session state for report builder."""
    if "report_config" not in st.session_state:
        st.session_state.report_config = {
            "title": "",
            "template": "standard",
            "sections": [],
            "data_sources": {},
            "metadata": {},
            "created_at": None,
            "modified_at": None,
        }
    if "available_sections" not in st.session_state:
        st.session_state.available_sections = get_available_sections()
    if "available_templates" not in st.session_state:
        st.session_state.available_templates = get_available_templates()
    if "preview_mode" not in st.session_state:
        st.session_state.preview_mode = False
    if "saved_configurations" not in st.session_state:
        st.session_state.saved_configurations = []


def get_available_sections() -> List[Dict[str, Any]]:
    """Get available report sections.

    Returns:
        List of available section definitions.
    """
    return [
        {
            "id": "executive_summary",
            "name": "Executive Summary",
            "description": "High-level overview of test results",
            "required_data": ["summary_stats"],
            "category": "overview",
        },
        {
            "id": "test_configuration",
            "name": "Test Configuration",
            "description": "Equipment setup and test parameters",
            "required_data": ["equipment_info", "test_parameters"],
            "category": "configuration",
        },
        {
            "id": "iv_curve_analysis",
            "name": "IV Curve Analysis",
            "description": "Current-voltage characteristic analysis",
            "required_data": ["iv_curve_data"],
            "category": "analysis",
        },
        {
            "id": "performance_metrics",
            "name": "Performance Metrics",
            "description": "Efficiency, fill factor, and other metrics",
            "required_data": ["performance_data"],
            "category": "analysis",
        },
        {
            "id": "insulation_testing",
            "name": "Insulation Testing",
            "description": "Insulation resistance test results",
            "required_data": ["insulation_data"],
            "category": "testing",
        },
        {
            "id": "visual_inspection",
            "name": "Visual Inspection",
            "description": "Physical inspection findings",
            "required_data": ["inspection_photos", "inspection_notes"],
            "category": "inspection",
        },
        {
            "id": "environmental_conditions",
            "name": "Environmental Conditions",
            "description": "Temperature, irradiance, and weather data",
            "required_data": ["environmental_data"],
            "category": "conditions",
        },
        {
            "id": "compliance_verification",
            "name": "Compliance Verification",
            "description": "Standards and regulatory compliance",
            "required_data": ["compliance_data"],
            "category": "compliance",
        },
        {
            "id": "recommendations",
            "name": "Recommendations",
            "description": "Findings and recommended actions",
            "required_data": ["findings"],
            "category": "conclusions",
        },
        {
            "id": "appendix",
            "name": "Appendix",
            "description": "Supporting data and documentation",
            "required_data": [],
            "category": "supplemental",
        },
    ]


def get_available_templates() -> Dict[str, Dict[str, Any]]:
    """Get available report templates.

    Returns:
        Dictionary of template definitions.
    """
    return {
        "standard": {
            "name": "Standard Report",
            "description": "Comprehensive standard PV test report",
            "default_sections": [
                "executive_summary",
                "test_configuration",
                "iv_curve_analysis",
                "performance_metrics",
                "environmental_conditions",
                "recommendations",
            ],
        },
        "quick": {
            "name": "Quick Report",
            "description": "Abbreviated report for routine testing",
            "default_sections": [
                "executive_summary",
                "performance_metrics",
                "recommendations",
            ],
        },
        "compliance": {
            "name": "Compliance Report",
            "description": "Regulatory compliance-focused report",
            "default_sections": [
                "executive_summary",
                "test_configuration",
                "compliance_verification",
                "recommendations",
                "appendix",
            ],
        },
        "detailed": {
            "name": "Detailed Analysis Report",
            "description": "In-depth technical analysis report",
            "default_sections": [
                "executive_summary",
                "test_configuration",
                "iv_curve_analysis",
                "performance_metrics",
                "insulation_testing",
                "visual_inspection",
                "environmental_conditions",
                "compliance_verification",
                "recommendations",
                "appendix",
            ],
        },
        "custom": {
            "name": "Custom Report",
            "description": "Build your own custom report",
            "default_sections": [],
        },
    }


def render_template_selector() -> None:
    """Render template selection interface."""
    st.subheader("Select Report Template")

    templates = st.session_state.available_templates

    # Display templates as cards
    cols = st.columns(3)

    for idx, (template_id, template_info) in enumerate(templates.items()):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"**{template_info['name']}**")
                st.caption(template_info["description"])

                if st.button(
                    "Select",
                    key=f"select_template_{template_id}",
                    use_container_width=True,
                ):
                    st.session_state.report_config["template"] = template_id
                    st.session_state.report_config["sections"] = (
                        template_info["default_sections"].copy()
                    )
                    st.success(f"Template '{template_info['name']}' selected")
                    st.rerun()

    # Show current selection
    current_template = st.session_state.report_config["template"]
    if current_template:
        st.info(
            f"Current template: **{templates[current_template]['name']}**"
        )


def render_section_selector() -> None:
    """Render section selection interface."""
    st.subheader("Configure Report Sections")

    sections = st.session_state.available_sections
    selected_sections = st.session_state.report_config["sections"]

    # Group sections by category
    categories = {}
    for section in sections:
        category = section["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(section)

    # Section selection
    st.write("**Available Sections:**")

    for category, category_sections in categories.items():
        with st.expander(f"{category.title()} Sections", expanded=True):
            for section in category_sections:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"**{section['name']}**")
                    st.caption(section["description"])

                with col2:
                    is_selected = section["id"] in selected_sections

                    if is_selected:
                        if st.button(
                            "Remove",
                            key=f"remove_{section['id']}",
                            use_container_width=True,
                        ):
                            selected_sections.remove(section["id"])
                            st.rerun()
                    else:
                        if st.button(
                            "Add",
                            key=f"add_{section['id']}",
                            use_container_width=True,
                        ):
                            selected_sections.append(section["id"])
                            st.rerun()

                with col3:
                    if is_selected:
                        position = selected_sections.index(section["id"])
                        st.caption(f"Position: {position + 1}")

    # Section ordering
    if selected_sections:
        st.divider()
        st.write("**Section Order:**")

        # Create reorderable list
        for idx, section_id in enumerate(selected_sections):
            section = next(s for s in sections if s["id"] == section_id)

            col1, col2, col3 = st.columns([5, 1, 1])

            with col1:
                st.write(f"{idx + 1}. {section['name']}")

            with col2:
                if idx > 0:
                    if st.button("↑", key=f"up_{section_id}"):
                        selected_sections[idx], selected_sections[idx - 1] = (
                            selected_sections[idx - 1],
                            selected_sections[idx],
                        )
                        st.rerun()

            with col3:
                if idx < len(selected_sections) - 1:
                    if st.button("↓", key=f"down_{section_id}"):
                        selected_sections[idx], selected_sections[idx + 1] = (
                            selected_sections[idx + 1],
                            selected_sections[idx],
                        )
                        st.rerun()


def render_data_source_mapping() -> None:
    """Render data source mapping interface."""
    st.subheader("Map Data Sources")

    sections = st.session_state.available_sections
    selected_sections = st.session_state.report_config["sections"]
    data_sources = st.session_state.report_config["data_sources"]

    if not selected_sections:
        st.info("Select report sections first to configure data sources")
        return

    # Get all required data fields
    required_data = set()
    for section_id in selected_sections:
        section = next(s for s in sections if s["id"] == section_id)
        required_data.update(section["required_data"])

    if not required_data:
        st.info("Selected sections do not require data source mapping")
        return

    # TODO: Get available data sources from database
    available_sources = [
        "Recent Test Results",
        "Equipment Database",
        "Environmental Monitor",
        "Compliance Database",
        "Manual Input",
    ]

    st.write("**Required Data Mappings:**")

    for data_field in sorted(required_data):
        col1, col2 = st.columns([2, 3])

        with col1:
            st.write(f"**{data_field.replace('_', ' ').title()}**")

        with col2:
            current_source = data_sources.get(data_field, "")
            selected_source = st.selectbox(
                "Data Source",
                options=[""] + available_sources,
                index=(
                    available_sources.index(current_source) + 1
                    if current_source in available_sources
                    else 0
                ),
                key=f"source_{data_field}",
                label_visibility="collapsed",
            )

            if selected_source:
                data_sources[data_field] = selected_source

    # Show mapping summary
    if data_sources:
        st.divider()
        st.write("**Mapping Summary:**")

        mapping_df = pd.DataFrame([
            {"Data Field": k.replace("_", " ").title(), "Source": v}
            for k, v in data_sources.items()
        ])

        st.dataframe(mapping_df, hide_index=True, use_container_width=True)


def render_report_metadata() -> None:
    """Render report metadata configuration."""
    st.subheader("Report Information")

    metadata = st.session_state.report_config["metadata"]

    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input(
            "Report Title",
            value=metadata.get("title", ""),
            placeholder="Enter report title",
        )
        metadata["title"] = title

        author = st.text_input(
            "Author",
            value=metadata.get("author", ""),
            placeholder="Enter author name",
        )
        metadata["author"] = author

        project = st.text_input(
            "Project",
            value=metadata.get("project", ""),
            placeholder="Enter project name",
        )
        metadata["project"] = project

    with col2:
        report_date = st.date_input(
            "Report Date",
            value=metadata.get("report_date", datetime.now()),
        )
        metadata["report_date"] = report_date

        location = st.text_input(
            "Location",
            value=metadata.get("location", ""),
            placeholder="Enter site location",
        )
        metadata["location"] = location

        customer = st.text_input(
            "Customer",
            value=metadata.get("customer", ""),
            placeholder="Enter customer name",
        )
        metadata["customer"] = customer

    # Additional metadata
    with st.expander("Additional Metadata"):
        description = st.text_area(
            "Description",
            value=metadata.get("description", ""),
            placeholder="Enter report description",
        )
        metadata["description"] = description

        tags = st.text_input(
            "Tags",
            value=metadata.get("tags", ""),
            placeholder="Enter tags (comma-separated)",
        )
        metadata["tags"] = tags


def render_preview() -> None:
    """Render report preview."""
    st.subheader("Report Preview")

    config = st.session_state.report_config

    if not config["sections"]:
        st.info("Add sections to see preview")
        return

    # Preview tabs
    tab1, tab2 = st.tabs(["Visual Preview", "JSON Configuration"])

    with tab1:
        # Visual preview of report structure
        st.write("**Report Structure:**")

        # Title and metadata
        st.markdown(f"# {config['metadata'].get('title', 'Untitled Report')}")
        st.caption(
            f"Template: {st.session_state.available_templates[config['template']]['name']}"
        )

        metadata = config["metadata"]
        if metadata:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Author:** {metadata.get('author', 'N/A')}")
            with col2:
                st.write(f"**Project:** {metadata.get('project', 'N/A')}")
            with col3:
                st.write(f"**Date:** {metadata.get('report_date', 'N/A')}")

        st.divider()

        # Sections preview
        sections = st.session_state.available_sections
        for idx, section_id in enumerate(config["sections"]):
            section = next(s for s in sections if s["id"] == section_id)

            with st.expander(f"{idx + 1}. {section['name']}", expanded=False):
                st.write(section["description"])

                if section["required_data"]:
                    st.write("**Required Data:**")
                    for data_field in section["required_data"]:
                        data_source = config["data_sources"].get(data_field, "Not mapped")
                        st.write(f"- {data_field}: {data_source}")

    with tab2:
        # JSON configuration
        st.json(config)


def render_save_load_controls() -> None:
    """Render save and load configuration controls."""
    st.subheader("Configuration Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        config_name = st.text_input(
            "Configuration Name",
            placeholder="Enter name to save",
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Save Configuration", use_container_width=True):
            if config_name:
                save_configuration(config_name)
                st.success(f"Configuration '{config_name}' saved")
            else:
                st.error("Please enter a configuration name")

    with col3:
        # TODO: Load from database
        saved_configs = ["Default Config", "Weekly Report", "Compliance Template"]

        selected_config = st.selectbox(
            "Load Configuration",
            options=[""] + saved_configs,
        )

        if selected_config:
            load_configuration(selected_config)


def save_configuration(name: str) -> None:
    """Save current report configuration.

    Args:
        name: Name for the saved configuration.
    """
    config = st.session_state.report_config.copy()
    config["name"] = name
    config["saved_at"] = datetime.now().isoformat()

    # TODO: Save to database
    st.session_state.saved_configurations.append(config)


def load_configuration(name: str) -> None:
    """Load saved report configuration.

    Args:
        name: Name of the configuration to load.
    """
    # TODO: Load from database
    st.info(f"Loading configuration: {name}")


def render_action_buttons() -> None:
    """Render action buttons for report generation."""
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Generate Report", use_container_width=True, type="primary"):
            if validate_report_config():
                st.success("Generating report...")
                # TODO: Trigger report generation
            else:
                st.error("Please complete all required configuration")

    with col2:
        if st.button("Preview Report", use_container_width=True):
            st.session_state.preview_mode = True
            st.rerun()

    with col3:
        if st.button("Clear Configuration", use_container_width=True):
            if st.confirm("Are you sure you want to clear the configuration?"):
                initialize_report_builder_state()
                st.rerun()

    with col4:
        if st.button("Export Config", use_container_width=True):
            export_configuration()


def validate_report_config() -> bool:
    """Validate report configuration.

    Returns:
        True if configuration is valid, False otherwise.
    """
    config = st.session_state.report_config

    # Check required fields
    if not config["metadata"].get("title"):
        return False

    if not config["sections"]:
        return False

    # Check data source mappings
    sections = st.session_state.available_sections
    required_data = set()
    for section_id in config["sections"]:
        section = next(s for s in sections if s["id"] == section_id)
        required_data.update(section["required_data"])

    for data_field in required_data:
        if data_field not in config["data_sources"]:
            return False

    return True


def export_configuration() -> None:
    """Export report configuration as JSON."""
    config = st.session_state.report_config

    # Convert to JSON
    config_json = json.dumps(config, indent=2, default=str)

    # Create download button
    st.download_button(
        label="Download Configuration",
        data=config_json,
        file_name=f"report_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )


def render_report_builder() -> None:
    """Render the report builder interface."""
    # Initialize state
    initialize_report_builder_state()

    # Page header
    st.title("Report Builder")
    st.write("Create custom PV test reports with interactive configuration")

    # Main layout tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Template",
        "Sections",
        "Data Sources",
        "Metadata",
        "Preview",
    ])

    with tab1:
        render_template_selector()

    with tab2:
        render_section_selector()

    with tab3:
        render_data_source_mapping()

    with tab4:
        render_report_metadata()

    with tab5:
        render_preview()

    st.divider()

    # Save/Load controls
    render_save_load_controls()

    # Action buttons
    render_action_buttons()


if __name__ == "__main__":
    render_report_builder()
