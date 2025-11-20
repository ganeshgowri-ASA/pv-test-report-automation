"""Reusable Form Components.

This module provides reusable form components for consistent user input
across the application.
"""

import streamlit as st
from typing import Any, List, Optional, Dict, Callable, Tuple
from datetime import date, time, datetime


def create_form_field(
    field_type: str,
    label: str,
    key: Optional[str] = None,
    default_value: Any = None,
    required: bool = False,
    help_text: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create a form field with validation.

    Args:
        field_type: Type of field ('text', 'number', 'date', 'select', etc.).
        label: Field label.
        key: Unique key for the field.
        default_value: Default value.
        required: Whether field is required.
        help_text: Help text for the field.
        **kwargs: Additional arguments for the specific field type.

    Returns:
        Field value.
    """
    # Add required indicator
    if required:
        label = f"{label} *"

    value = None

    if field_type == "text":
        value = st.text_input(
            label,
            value=default_value or "",
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "textarea":
        value = st.text_area(
            label,
            value=default_value or "",
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "number":
        value = st.number_input(
            label,
            value=default_value if default_value is not None else 0,
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "select":
        options = kwargs.pop("options", [])
        value = st.selectbox(
            label,
            options=options,
            index=options.index(default_value) if default_value in options else 0,
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "multiselect":
        options = kwargs.pop("options", [])
        value = st.multiselect(
            label,
            options=options,
            default=default_value or [],
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "checkbox":
        value = st.checkbox(
            label,
            value=default_value or False,
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "date":
        value = st.date_input(
            label,
            value=default_value or date.today(),
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "time":
        value = st.time_input(
            label,
            value=default_value or time(),
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "slider":
        value = st.slider(
            label,
            key=key,
            help=help_text,
            **kwargs,
        )
    elif field_type == "radio":
        options = kwargs.pop("options", [])
        value = st.radio(
            label,
            options=options,
            index=options.index(default_value) if default_value in options else 0,
            key=key,
            help=help_text,
            **kwargs,
        )

    # Validation for required fields
    if required and not value:
        st.error(f"{label.replace(' *', '')} is required")

    return value


def create_file_uploader(
    label: str,
    accepted_types: Optional[List[str]] = None,
    multiple: bool = False,
    key: Optional[str] = None,
    help_text: Optional[str] = None,
) -> Any:
    """Create a file uploader with validation.

    Args:
        label: Uploader label.
        accepted_types: List of accepted file extensions.
        multiple: Whether to accept multiple files.
        key: Unique key for the uploader.
        help_text: Help text.

    Returns:
        Uploaded file(s).
    """
    return st.file_uploader(
        label,
        type=accepted_types,
        accept_multiple_files=multiple,
        key=key,
        help=help_text,
    )


def create_validated_form(
    form_fields: List[Dict[str, Any]],
    submit_label: str = "Submit",
    key: Optional[str] = None,
    on_submit: Optional[Callable] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """Create a validated form with multiple fields.

    Args:
        form_fields: List of field configurations.
        submit_label: Submit button label.
        key: Unique key for the form.
        on_submit: Callback function when form is submitted.

    Returns:
        Tuple of (is_submitted, form_values).
    """
    form_values = {}

    with st.form(key=key or "form"):
        for field_config in form_fields:
            field_type = field_config.pop("type")
            field_key = field_config.pop("key")
            field_label = field_config.pop("label")

            value = create_form_field(
                field_type,
                field_label,
                key=f"{key}_{field_key}" if key else field_key,
                **field_config,
            )

            form_values[field_key] = value

        submitted = st.form_submit_button(submit_label)

        if submitted:
            # Validate all fields
            is_valid = True
            for field_config in form_fields:
                if field_config.get("required", False):
                    field_key = field_config["key"]
                    if not form_values.get(field_key):
                        is_valid = False
                        break

            if is_valid:
                if on_submit:
                    on_submit(form_values)
                return True, form_values
            else:
                st.error("Please fill in all required fields")
                return False, form_values

    return False, form_values


def create_search_box(
    placeholder: str = "Search...",
    key: Optional[str] = None,
    on_change: Optional[Callable] = None,
) -> str:
    """Create a search box.

    Args:
        placeholder: Placeholder text.
        key: Unique key for the search box.
        on_change: Callback when search text changes.

    Returns:
        Search query string.
    """
    search_query = st.text_input(
        "",
        placeholder=placeholder,
        key=key,
        label_visibility="collapsed",
    )

    if on_change and search_query:
        on_change(search_query)

    return search_query


def create_filter_group(
    filters: Dict[str, Dict[str, Any]],
    key: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a group of filter controls.

    Args:
        filters: Dictionary of filter configurations.
        key: Unique key prefix for filters.

    Returns:
        Dictionary of filter values.
    """
    filter_values = {}

    st.write("**Filters:**")

    # Calculate number of columns based on number of filters
    num_filters = len(filters)
    num_cols = min(num_filters, 3)
    cols = st.columns(num_cols)

    for idx, (filter_name, filter_config) in enumerate(filters.items()):
        with cols[idx % num_cols]:
            filter_type = filter_config.pop("type", "select")
            filter_label = filter_config.pop("label", filter_name)

            value = create_form_field(
                filter_type,
                filter_label,
                key=f"{key}_{filter_name}" if key else filter_name,
                **filter_config,
            )

            filter_values[filter_name] = value

    return filter_values


def create_pagination_controls(
    total_items: int,
    page_size: int = 10,
    key: Optional[str] = None,
) -> Tuple[int, int, int]:
    """Create pagination controls.

    Args:
        total_items: Total number of items.
        page_size: Items per page.
        key: Unique key for pagination.

    Returns:
        Tuple of (current_page, start_index, end_index).
    """
    total_pages = (total_items - 1) // page_size + 1

    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        if st.button("← Previous", key=f"{key}_prev" if key else None):
            if "page" not in st.session_state:
                st.session_state.page = 1
            st.session_state.page = max(1, st.session_state.page - 1)

    with col2:
        if "page" not in st.session_state:
            st.session_state.page = 1

        page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.page,
            key=f"{key}_page" if key else None,
            label_visibility="collapsed",
        )
        st.session_state.page = page

        st.caption(f"of {total_pages}")

    with col3:
        if st.button("Next →", key=f"{key}_next" if key else None):
            st.session_state.page = min(total_pages, st.session_state.page + 1)

    start_idx = (st.session_state.page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)

    return st.session_state.page, start_idx, end_idx


def create_date_range_picker(
    label: str = "Date Range",
    key: Optional[str] = None,
    default_days: int = 7,
) -> Tuple[date, date]:
    """Create a date range picker.

    Args:
        label: Label for the date range picker.
        key: Unique key.
        default_days: Default number of days in range.

    Returns:
        Tuple of (start_date, end_date).
    """
    st.write(f"**{label}:**")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "From",
            value=date.today() - pd.Timedelta(days=default_days),
            key=f"{key}_start" if key else None,
        )

    with col2:
        end_date = st.date_input(
            "To",
            value=date.today(),
            key=f"{key}_end" if key else None,
        )

    return start_date, end_date


def create_confirmation_dialog(
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    key: Optional[str] = None,
) -> bool:
    """Create a confirmation dialog.

    Args:
        message: Confirmation message.
        confirm_label: Confirm button label.
        cancel_label: Cancel button label.
        key: Unique key.

    Returns:
        True if confirmed, False otherwise.
    """
    st.warning(message)

    col1, col2 = st.columns(2)

    with col1:
        if st.button(confirm_label, key=f"{key}_confirm" if key else None):
            return True

    with col2:
        if st.button(cancel_label, key=f"{key}_cancel" if key else None):
            return False

    return False


def create_multi_step_form(
    steps: List[Dict[str, Any]],
    key: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Create a multi-step form.

    Args:
        steps: List of step configurations.
        key: Unique key for the form.

    Returns:
        Tuple of (current_step, form_data).
    """
    # Initialize session state
    if f"{key}_step" not in st.session_state:
        st.session_state[f"{key}_step"] = 0
    if f"{key}_data" not in st.session_state:
        st.session_state[f"{key}_data"] = {}

    current_step = st.session_state[f"{key}_step"]
    form_data = st.session_state[f"{key}_data"]

    # Progress indicator
    progress = (current_step + 1) / len(steps)
    st.progress(progress)
    st.caption(f"Step {current_step + 1} of {len(steps)}")

    # Display current step
    step_config = steps[current_step]
    st.subheader(step_config["title"])

    if "description" in step_config:
        st.write(step_config["description"])

    # Render fields for current step
    step_data = {}
    for field_config in step_config["fields"]:
        field_type = field_config["type"]
        field_key = field_config["key"]
        field_label = field_config["label"]

        # Get default value from saved data
        default_value = form_data.get(field_key, field_config.get("default"))

        value = create_form_field(
            field_type,
            field_label,
            key=f"{key}_{field_key}",
            default_value=default_value,
            **{k: v for k, v in field_config.items() if k not in ["type", "key", "label"]},
        )

        step_data[field_key] = value

    # Update form data
    form_data.update(step_data)
    st.session_state[f"{key}_data"] = form_data

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if current_step > 0:
            if st.button("← Previous", key=f"{key}_prev"):
                st.session_state[f"{key}_step"] = current_step - 1
                st.rerun()

    with col3:
        if current_step < len(steps) - 1:
            if st.button("Next →", key=f"{key}_next"):
                st.session_state[f"{key}_step"] = current_step + 1
                st.rerun()
        else:
            if st.button("Finish", key=f"{key}_finish", type="primary"):
                # Form completed
                st.session_state[f"{key}_step"] = 0
                return current_step, form_data

    return current_step, form_data


def create_dynamic_list(
    label: str,
    field_type: str = "text",
    key: Optional[str] = None,
    max_items: int = 10,
    **field_kwargs,
) -> List[Any]:
    """Create a dynamic list where users can add/remove items.

    Args:
        label: Label for the list.
        field_type: Type of field for items.
        key: Unique key.
        max_items: Maximum number of items.
        **field_kwargs: Additional arguments for field type.

    Returns:
        List of values.
    """
    # Initialize session state
    if f"{key}_items" not in st.session_state:
        st.session_state[f"{key}_items"] = []

    st.write(f"**{label}:**")

    items = st.session_state[f"{key}_items"]

    # Display existing items
    for idx, item in enumerate(items):
        col1, col2 = st.columns([4, 1])

        with col1:
            value = create_form_field(
                field_type,
                "",
                key=f"{key}_item_{idx}",
                default_value=item,
                label_visibility="collapsed",
                **field_kwargs,
            )
            items[idx] = value

        with col2:
            if st.button("Remove", key=f"{key}_remove_{idx}"):
                items.pop(idx)
                st.rerun()

    # Add new item button
    if len(items) < max_items:
        if st.button(f"+ Add {label}", key=f"{key}_add"):
            items.append(None)
            st.rerun()

    st.session_state[f"{key}_items"] = items

    return items
