"""Reusable Chart Components.

This module provides reusable chart components using Plotly for
interactive visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Union


def create_kpi_card(
    title: str,
    value: Union[int, float, str],
    change: Optional[float] = None,
    trend: Optional[str] = None,
    period: Optional[str] = None,
    prefix: str = "",
    suffix: str = "",
) -> None:
    """Create a KPI card with metric display.

    Args:
        title: KPI title.
        value: Current value.
        change: Percentage change.
        trend: Trend indicator ('up', 'down', 'stable').
        period: Period for comparison.
        prefix: Value prefix (e.g., '$').
        suffix: Value suffix (e.g., '%').
    """
    with st.container():
        st.markdown(f"**{title}**")

        # Display value
        value_str = f"{prefix}{value}{suffix}"
        st.markdown(f"<h2 style='margin:0;'>{value_str}</h2>", unsafe_allow_html=True)

        # Display change and trend
        if change is not None:
            color = "green" if change >= 0 else "red"
            arrow = "↑" if change >= 0 else "↓"

            if trend == "down" and change < 0:
                # For metrics where down is good (e.g., processing time)
                color = "green"
            elif trend == "down" and change > 0:
                color = "red"

            st.markdown(
                f"<span style='color:{color};'>{arrow} {abs(change):.1f}%</span> {period or ''}",
                unsafe_allow_html=True,
            )


def create_line_chart(
    data: pd.DataFrame,
    x: str,
    y: Union[str, List[str]],
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    height: int = 400,
) -> go.Figure:
    """Create a line chart.

    Args:
        data: DataFrame containing the data.
        x: Column name for x-axis.
        y: Column name(s) for y-axis.
        title: Chart title.
        x_label: X-axis label.
        y_label: Y-axis label.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    if isinstance(y, str):
        y = [y]

    for y_col in y:
        fig.add_trace(
            go.Scatter(
                x=data[x],
                y=data[y_col],
                mode="lines+markers",
                name=y_col,
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=x_label or x,
        yaxis_title=y_label,
        height=height,
        hovermode="x unified",
    )

    return fig


def create_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    color: Optional[str] = None,
    orientation: str = "v",
    height: int = 400,
) -> go.Figure:
    """Create a bar chart.

    Args:
        data: DataFrame containing the data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        x_label: X-axis label.
        y_label: Y-axis label.
        color: Column name for color grouping.
        orientation: 'v' for vertical, 'h' for horizontal.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        labels={x: x_label or x, y: y_label or y},
        orientation=orientation,
        height=height,
    )

    return fig


def create_pie_chart(
    data: pd.DataFrame,
    values: str,
    names: str,
    title: str = "",
    height: int = 400,
    hole: float = 0,
) -> go.Figure:
    """Create a pie or donut chart.

    Args:
        data: DataFrame containing the data.
        values: Column name for values.
        names: Column name for labels.
        title: Chart title.
        height: Chart height in pixels.
        hole: Size of hole for donut chart (0-1).

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure(
        data=[
            go.Pie(
                labels=data[names],
                values=data[values],
                hole=hole,
            )
        ]
    )

    fig.update_layout(
        title=title,
        height=height,
    )

    return fig


def create_status_chart(
    data: pd.DataFrame,
    category: str,
    value: str,
    title: str = "Status Distribution",
    height: int = 400,
) -> go.Figure:
    """Create a status distribution chart (donut chart).

    Args:
        data: DataFrame containing status data.
        category: Column name for categories.
        value: Column name for values.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    colors = {
        "Passed": "#28a745",
        "Failed": "#dc3545",
        "In Progress": "#ffc107",
        "Pending": "#6c757d",
        "Active": "#28a745",
        "Idle": "#6c757d",
        "Maintenance": "#ffc107",
    }

    color_sequence = [
        colors.get(cat, "#007bff") for cat in data[category]
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=data[category],
                values=data[value],
                hole=0.4,
                marker=dict(colors=color_sequence),
            )
        ]
    )

    fig.update_layout(
        title=title,
        height=height,
    )

    return fig


def create_timeline_chart(
    data: pd.DataFrame,
    x: str,
    y_columns: List[str],
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Create a timeline chart with multiple series.

    Args:
        data: DataFrame containing time series data.
        x: Column name for time axis.
        y_columns: List of column names to plot.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    for y_col in y_columns:
        fig.add_trace(
            go.Scatter(
                x=data[x],
                y=data[y_col],
                mode="lines+markers",
                name=y_col.replace("_", " ").title(),
                fill="tonexty" if len(y_columns) > 1 else None,
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Count",
        height=height,
        hovermode="x unified",
    )

    return fig


def create_performance_chart(
    data: pd.DataFrame,
    title: str = "Performance Metrics",
    height: int = 400,
) -> go.Figure:
    """Create a performance comparison chart.

    Args:
        data: DataFrame with columns 'metric', 'current', 'target'.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Current",
            x=data["metric"],
            y=data["current"],
            marker_color="#007bff",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Target",
            x=data["metric"],
            y=data["target"],
            marker_color="#28a745",
        )
    )

    fig.update_layout(
        title=title,
        barmode="group",
        height=height,
        xaxis_title="Metric",
        yaxis_title="Value",
    )

    return fig


def create_gauge_chart(
    value: float,
    title: str = "",
    min_value: float = 0,
    max_value: float = 100,
    thresholds: Optional[Dict[str, float]] = None,
    height: int = 300,
) -> go.Figure:
    """Create a gauge chart.

    Args:
        value: Current value.
        title: Chart title.
        min_value: Minimum value.
        max_value: Maximum value.
        thresholds: Dictionary of threshold values
            (e.g., {'low': 30, 'medium': 70}).
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    if thresholds is None:
        thresholds = {"low": max_value * 0.3, "medium": max_value * 0.7}

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={"text": title},
            delta={"reference": max_value * 0.8},
            gauge={
                "axis": {"range": [min_value, max_value]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [min_value, thresholds["low"]], "color": "lightgray"},
                    {"range": [thresholds["low"], thresholds["medium"]], "color": "gray"},
                    {"range": [thresholds["medium"], max_value], "color": "darkgray"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": max_value * 0.9,
                },
            },
        )
    )

    fig.update_layout(height=height)

    return fig


def create_heatmap(
    data: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Create a heatmap.

    Args:
        data: DataFrame containing the data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        z: Column name for values.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    # Pivot data for heatmap
    pivot_data = data.pivot(index=y, columns=x, values=z)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale="Viridis",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y,
        height=height,
    )

    return fig


def create_scatter_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: Optional[str] = None,
    size: Optional[str] = None,
    height: int = 400,
) -> go.Figure:
    """Create a scatter plot.

    Args:
        data: DataFrame containing the data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        color: Column name for color grouping.
        size: Column name for marker size.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        size=size,
        title=title,
        height=height,
    )

    return fig


def create_box_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Create a box plot.

    Args:
        data: DataFrame containing the data.
        x: Column name for categories.
        y: Column name for values.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = px.box(
        data,
        x=x,
        y=y,
        title=title,
        height=height,
    )

    return fig


def create_histogram(
    data: pd.DataFrame,
    column: str,
    title: str = "",
    bins: int = 20,
    height: int = 400,
) -> go.Figure:
    """Create a histogram.

    Args:
        data: DataFrame containing the data.
        column: Column name for values.
        title: Chart title.
        bins: Number of bins.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = px.histogram(
        data,
        x=column,
        nbins=bins,
        title=title,
        height=height,
    )

    return fig


def create_area_chart(
    data: pd.DataFrame,
    x: str,
    y: Union[str, List[str]],
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Create an area chart.

    Args:
        data: DataFrame containing the data.
        x: Column name for x-axis.
        y: Column name(s) for y-axis.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    if isinstance(y, str):
        y = [y]

    fig = go.Figure()

    for y_col in y:
        fig.add_trace(
            go.Scatter(
                x=data[x],
                y=data[y_col],
                mode="lines",
                name=y_col,
                fill="tonexty",
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=x,
        height=height,
        hovermode="x unified",
    )

    return fig


def create_multi_axis_chart(
    data: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    y1_label: str = "",
    y2_label: str = "",
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Create a chart with multiple y-axes.

    Args:
        data: DataFrame containing the data.
        x: Column name for x-axis.
        y1: Column name for first y-axis.
        y2: Column name for second y-axis.
        y1_label: Label for first y-axis.
        y2_label: Label for second y-axis.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y1],
            name=y1_label or y1,
            yaxis="y1",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y2],
            name=y2_label or y2,
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(title=x),
        yaxis=dict(
            title=y1_label or y1,
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4"),
        ),
        yaxis2=dict(
            title=y2_label or y2,
            titlefont=dict(color="#ff7f0e"),
            tickfont=dict(color="#ff7f0e"),
            overlaying="y",
            side="right",
        ),
        height=height,
    )

    return fig


def create_waterfall_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Create a waterfall chart.

    Args:
        data: DataFrame containing the data.
        x: Column name for categories.
        y: Column name for values.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure(
        go.Waterfall(
            x=data[x],
            y=data[y],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        )
    )

    fig.update_layout(
        title=title,
        height=height,
    )

    return fig
