"""Reusable Data Table Components.

This module provides reusable data table components with pagination,
filtering, sorting, and custom column configurations.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Callable


def create_data_table(
    data: pd.DataFrame,
    page_size: int = 10,
    column_config: Optional[Dict[str, Any]] = None,
    hide_index: bool = True,
    use_container_width: bool = True,
    key: Optional[str] = None,
) -> None:
    """Create a paginated data table with custom configuration.

    Args:
        data: DataFrame to display.
        page_size: Number of rows per page.
        column_config: Custom column configuration.
        hide_index: Whether to hide the index column.
        use_container_width: Whether to use full container width.
        key: Unique key for the table.
    """
    if data.empty:
        st.info("No data to display")
        return

    # Pagination
    total_rows = len(data)
    total_pages = (total_rows - 1) // page_size + 1

    if total_pages > 1:
        col1, col2, col3 = st.columns([2, 1, 2])

        with col2:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=1,
                key=f"{key}_page" if key else None,
            )

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)

        paginated_data = data.iloc[start_idx:end_idx]

        st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_rows} rows")
    else:
        paginated_data = data

    # Display table
    st.dataframe(
        paginated_data,
        column_config=column_config,
        hide_index=hide_index,
        use_container_width=use_container_width,
    )


def create_sortable_table(
    data: pd.DataFrame,
    default_sort_column: Optional[str] = None,
    default_sort_ascending: bool = True,
    page_size: int = 10,
    column_config: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> None:
    """Create a sortable data table.

    Args:
        data: DataFrame to display.
        default_sort_column: Column to sort by default.
        default_sort_ascending: Sort order.
        page_size: Number of rows per page.
        column_config: Custom column configuration.
        key: Unique key for the table.
    """
    if data.empty:
        st.info("No data to display")
        return

    # Sort controls
    col1, col2 = st.columns([3, 1])

    with col1:
        sort_column = st.selectbox(
            "Sort by",
            options=data.columns.tolist(),
            index=(
                data.columns.tolist().index(default_sort_column)
                if default_sort_column
                else 0
            ),
            key=f"{key}_sort_col" if key else None,
        )

    with col2:
        sort_order = st.selectbox(
            "Order",
            options=["Ascending", "Descending"],
            index=0 if default_sort_ascending else 1,
            key=f"{key}_sort_order" if key else None,
        )

    # Sort data
    sorted_data = data.sort_values(
        by=sort_column,
        ascending=(sort_order == "Ascending"),
    )

    # Display table
    create_data_table(
        sorted_data,
        page_size=page_size,
        column_config=column_config,
        key=key,
    )


def create_filterable_table(
    data: pd.DataFrame,
    filter_columns: List[str],
    page_size: int = 10,
    column_config: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> pd.DataFrame:
    """Create a filterable data table.

    Args:
        data: DataFrame to display.
        filter_columns: Columns to enable filtering on.
        page_size: Number of rows per page.
        column_config: Custom column configuration.
        key: Unique key for the table.

    Returns:
        Filtered DataFrame.
    """
    if data.empty:
        st.info("No data to display")
        return data

    # Create filters
    st.write("**Filters:**")

    filters = {}
    cols = st.columns(min(len(filter_columns), 3))

    for idx, column in enumerate(filter_columns):
        with cols[idx % 3]:
            if data[column].dtype == "object":
                # Categorical filter
                unique_values = data[column].unique().tolist()
                selected = st.multiselect(
                    column,
                    options=unique_values,
                    default=unique_values,
                    key=f"{key}_filter_{column}" if key else None,
                )
                filters[column] = selected
            else:
                # Numeric filter
                min_val = data[column].min()
                max_val = data[column].max()
                range_vals = st.slider(
                    column,
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=(float(min_val), float(max_val)),
                    key=f"{key}_filter_{column}" if key else None,
                )
                filters[column] = range_vals

    # Apply filters
    filtered_data = data.copy()

    for column, filter_value in filters.items():
        if data[column].dtype == "object":
            filtered_data = filtered_data[filtered_data[column].isin(filter_value)]
        else:
            filtered_data = filtered_data[
                (filtered_data[column] >= filter_value[0]) &
                (filtered_data[column] <= filter_value[1])
            ]

    st.caption(f"Showing {len(filtered_data)} of {len(data)} rows")

    # Display table
    create_data_table(
        filtered_data,
        page_size=page_size,
        column_config=column_config,
        key=key,
    )

    return filtered_data


def create_editable_table(
    data: pd.DataFrame,
    editable_columns: List[str],
    on_change: Optional[Callable] = None,
    key: Optional[str] = None,
) -> pd.DataFrame:
    """Create an editable data table.

    Args:
        data: DataFrame to display.
        editable_columns: Columns that can be edited.
        on_change: Callback function when data changes.
        key: Unique key for the table.

    Returns:
        Edited DataFrame.
    """
    if data.empty:
        st.info("No data to display")
        return data

    # Configure editable columns
    column_config = {}
    for col in data.columns:
        if col in editable_columns:
            column_config[col] = st.column_config.TextColumn(
                col,
                help=f"Edit {col}",
                disabled=False,
            )

    # Display editable table
    edited_data = st.data_editor(
        data,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=key,
    )

    # Call on_change callback if provided
    if on_change and not edited_data.equals(data):
        on_change(edited_data)

    return edited_data


def create_selectable_table(
    data: pd.DataFrame,
    selection_mode: str = "single",
    page_size: int = 10,
    column_config: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> List[int]:
    """Create a table with row selection.

    Args:
        data: DataFrame to display.
        selection_mode: 'single' or 'multiple'.
        page_size: Number of rows per page.
        column_config: Custom column configuration.
        key: Unique key for the table.

    Returns:
        List of selected row indices.
    """
    if data.empty:
        st.info("No data to display")
        return []

    selected_rows = []

    for idx, row in data.iterrows():
        col1, col2 = st.columns([1, 19])

        with col1:
            if selection_mode == "single":
                if st.radio(
                    "",
                    options=[idx],
                    key=f"{key}_select_{idx}" if key else None,
                    label_visibility="collapsed",
                ):
                    selected_rows = [idx]
            else:
                if st.checkbox(
                    "",
                    key=f"{key}_select_{idx}" if key else None,
                    label_visibility="collapsed",
                ):
                    selected_rows.append(idx)

        with col2:
            # Display row data
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
            st.write(row_text)

    return selected_rows


def create_summary_table(
    data: pd.DataFrame,
    summary_columns: List[str],
    aggregations: Dict[str, str],
) -> None:
    """Create a summary table with aggregated statistics.

    Args:
        data: DataFrame to summarize.
        summary_columns: Columns to include in summary.
        aggregations: Dictionary mapping column to aggregation type
            (e.g., {'column': 'sum', 'column2': 'mean'}).
    """
    if data.empty:
        st.info("No data to summarize")
        return

    summary_data = {}

    for column in summary_columns:
        if column not in data.columns:
            continue

        agg_type = aggregations.get(column, "count")

        if agg_type == "sum":
            summary_data[column] = [data[column].sum()]
        elif agg_type == "mean":
            summary_data[column] = [data[column].mean()]
        elif agg_type == "median":
            summary_data[column] = [data[column].median()]
        elif agg_type == "min":
            summary_data[column] = [data[column].min()]
        elif agg_type == "max":
            summary_data[column] = [data[column].max()]
        elif agg_type == "count":
            summary_data[column] = [data[column].count()]
        elif agg_type == "unique":
            summary_data[column] = [data[column].nunique()]

    summary_df = pd.DataFrame(summary_data)

    st.write("**Summary Statistics:**")
    st.dataframe(summary_df, hide_index=True, use_container_width=True)


def create_comparison_table(
    data1: pd.DataFrame,
    data2: pd.DataFrame,
    label1: str = "Dataset 1",
    label2: str = "Dataset 2",
    highlight_differences: bool = True,
) -> None:
    """Create a side-by-side comparison table.

    Args:
        data1: First DataFrame.
        data2: Second DataFrame.
        label1: Label for first dataset.
        label2: Label for second dataset.
        highlight_differences: Whether to highlight differences.
    """
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**{label1}**")
        st.dataframe(data1, hide_index=True, use_container_width=True)

    with col2:
        st.write(f"**{label2}**")
        st.dataframe(data2, hide_index=True, use_container_width=True)

    if highlight_differences and data1.shape == data2.shape:
        st.write("**Differences:**")

        differences = []
        for idx in range(len(data1)):
            for col in data1.columns:
                if col in data2.columns:
                    if data1.iloc[idx][col] != data2.iloc[idx][col]:
                        differences.append({
                            "Row": idx,
                            "Column": col,
                            label1: data1.iloc[idx][col],
                            label2: data2.iloc[idx][col],
                        })

        if differences:
            diff_df = pd.DataFrame(differences)
            st.dataframe(diff_df, hide_index=True, use_container_width=True)
        else:
            st.success("No differences found")
