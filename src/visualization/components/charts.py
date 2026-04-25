"""Reusable Plotly chart builder functions with consistent styling."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


#  Consistent color palette across the dashboard 
APP_COLORS = {
    "PhonePe": "#5B21B6",
    "Google Pay": "#2563EB",
    "Paytm": "#0891B2",
    "CRED": "#1E293B",
    "Amazon Pay": "#D97706",
    "WhatsApp Pay": "#059669",
    "Others": "#94A3B8",
    "primary": "#2563EB",
    "secondary": "#7C3AED",
    "positive": "#059669",
    "negative": "#DC2626",
    "warning": "#D97706",
    "info": "#0284C7",
}

CLUSTER_COLORS = {
    "Very Low Adoption": "#DC2626",
    "Low Adoption": "#D97706",
    "Medium Adoption": "#16A34A",
    "High Adoption": "#059669",
}

CATEGORY_COLORS = {
    "Peer-to-Peer Payments": "#2563EB",
    "Merchant Payments": "#7C3AED",
    "Recharge & Bill Payments": "#059669",
    "Financial Services": "#D97706",
    "Others": "#94A3B8",
    "p2p_payments": "#2563EB",
    "merchant_payments": "#7C3AED",
    "recharge_bill_payments": "#059669",
    "financial_services": "#D97706",
    "others": "#94A3B8",
}

REGION_COLORS = {
    "South": "#2563EB",
    "West": "#D97706",
    "North": "#059669",
    "East": "#DC2626",
    "Northeast": "#7C3AED",
    "Central": "#0891B2",
    "Other": "#94A3B8",
}

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


def apply_common_layout(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Apply consistent layout styling to any Plotly figure."""
    layout = dict(
        template="plotly_white",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size=13,
            color="#334155",
        ),
        title_font=dict(size=15, color="#0f172a"),
        title_x=0,
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#e2e8f0"),
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
            font=dict(size=11, color="#475569"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    if height:
        layout["height"] = height
    fig.update_layout(**layout)
    fig.update_xaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0", linewidth=1)
    fig.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0", linewidth=1)
    return fig


#  Bar Charts 


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    color_discrete_map: dict | None = None,
    color_continuous_scale: str | None = None,
    text_auto: bool = True,
    orientation: str = "v",
    height: int | None = None,
) -> go.Figure:
    """Create a styled bar chart."""
    kwargs: dict = dict(
        x=x, y=y, title=title, orientation=orientation,
        text_auto=".2s" if text_auto else False,
    )
    if color:
        kwargs["color"] = color
    if color_discrete_map:
        kwargs["color_discrete_map"] = color_discrete_map
    if color_continuous_scale:
        kwargs["color"] = y if orientation == "v" else x
        kwargs["color_continuous_scale"] = color_continuous_scale

    fig = px.bar(df, **kwargs)
    fig.update_traces(textposition="outside")
    return apply_common_layout(fig, height)


def create_horizontal_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    color_discrete_map: dict | None = None,
    height: int | None = None,
) -> go.Figure:
    """Create a horizontal bar chart (e.g., app market share ranking)."""
    fig = px.bar(
        df, x=x, y=y, color=color,
        color_discrete_map=color_discrete_map,
        title=title, orientation="h", text_auto=".1f",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    return apply_common_layout(fig, height)


def create_grouped_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    barmode: str = "group",
    color_discrete_map: dict | None = None,
    height: int | None = None,
) -> go.Figure:
    """Create a grouped or stacked bar chart."""
    fig = px.bar(
        df, x=x, y=y, color=color, barmode=barmode,
        color_discrete_map=color_discrete_map, title=title,
        text_auto=".2s",
    )
    fig.update_traces(textposition="outside")
    return apply_common_layout(fig, height)


#  Line Charts 


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    area_fill: bool = False,
    markers: bool = True,
    color_discrete_map: dict | None = None,
    height: int | None = None,
) -> go.Figure:
    """Create a styled line chart, optionally with area fill."""
    if area_fill:
        fig = px.area(df, x=x, y=y, color=color, title=title, markers=markers,
                      color_discrete_map=color_discrete_map)
    else:
        fig = px.line(df, x=x, y=y, color=color, title=title, markers=markers,
                      color_discrete_map=color_discrete_map)
    return apply_common_layout(fig, height)


def create_stacked_area(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    color_discrete_map: dict | None = None,
    as_percent: bool = True,
    height: int | None = None,
) -> go.Figure:
    """Create a stacked area chart (e.g., market share over time)."""
    kwargs: dict = dict(x=x, y=y, color=color, title=title,
                        color_discrete_map=color_discrete_map or APP_COLORS)
    if as_percent:
        kwargs["groupnorm"] = "percent"
    fig = px.area(df, **kwargs)
    if as_percent:
        fig.update_layout(yaxis_title="Share (%)")
    return apply_common_layout(fig, height)


def create_multi_line(
    df: pd.DataFrame,
    x: str,
    y_cols: list[str],
    title: str,
    names: list[str] | None = None,
    colors: list[str] | None = None,
    height: int | None = None,
) -> go.Figure:
    """Create a multi-line chart from multiple y columns."""
    fig = go.Figure()
    names = names or y_cols
    default_colors = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626"]
    colors = colors or default_colors

    for i, (col, name) in enumerate(zip(y_cols, names)):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=name,
            line=dict(color=colors[i % len(colors)], width=2.5),
            mode="lines+markers",
        ))
    fig.update_layout(title=title)
    return apply_common_layout(fig, height)


#  Pie / Donut Charts 


def create_donut_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str,
    color_discrete_map: dict | None = None,
    height: int | None = None,
) -> go.Figure:
    """Create a donut chart with a hole in the center."""
    fig = px.pie(
        df, values=values, names=names, title=title,
        hole=0.45, color=names,
        color_discrete_map=color_discrete_map,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont_size=11)
    return apply_common_layout(fig, height)


#  Specialized Charts 


def create_dual_axis_chart(
    df: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    title: str,
    y1_name: str = "Series 1",
    y2_name: str = "Series 2",
    y1_color: str = "#1A73E8",
    y2_color: str = "#00C853",
    height: int | None = None,
) -> go.Figure:
    """Create a dual-axis line chart (e.g., UPI vs Cash)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df[x], y=df[y1], name=y1_name,
            line=dict(color=y1_color, width=2.5),
            mode="lines+markers",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df[x], y=df[y2], name=y2_name,
            line=dict(color=y2_color, width=2.5),
            mode="lines+markers",
        ),
        secondary_y=True,
    )

    fig.update_layout(title=title)
    fig.update_yaxes(title_text=y1_name, secondary_y=False)
    fig.update_yaxes(title_text=y2_name, secondary_y=True)
    return apply_common_layout(fig, height)


def create_hhi_trend(df: pd.DataFrame, x: str, y: str, title: str,
                     height: int | None = None) -> go.Figure:
    """Create HHI trend line with DOJ threshold annotations."""
    fig = go.Figure()

    fig.add_hrect(y0=0, y1=0.15, fillcolor="green", opacity=0.07,
                  line_width=0, annotation_text="Competitive",
                  annotation_position="top left")
    fig.add_hrect(y0=0.15, y1=0.25, fillcolor="orange", opacity=0.07,
                  line_width=0, annotation_text="Moderate",
                  annotation_position="top left")
    fig.add_hrect(y0=0.25, y1=0.5, fillcolor="red", opacity=0.07,
                  line_width=0, annotation_text="Highly Concentrated",
                  annotation_position="top left")

    fig.add_hline(y=0.15, line_dash="dash", line_color="green", opacity=0.5)
    fig.add_hline(y=0.25, line_dash="dash", line_color="red", opacity=0.5)

    fig.add_trace(go.Scatter(
        x=df[x], y=df[y], name="HHI Index",
        line=dict(color=APP_COLORS["primary"], width=3),
        mode="lines+markers", marker=dict(size=8),
    ))

    fig.update_layout(title=title, yaxis_title="HHI Value", yaxis_range=[0, 0.5])
    return apply_common_layout(fig, height)


def create_gauge(value: float, title: str, min_val: float = 0,
                 max_val: float = 1, thresholds: list | None = None,
                 height: int = 250) -> go.Figure:
    """Create a gauge/indicator chart (e.g., for HHI)."""
    steps = []
    if thresholds:
        colors = ["#00C853", "#FFA000", "#FF1744"]
        for i, (lo, hi) in enumerate(thresholds):
            steps.append(dict(range=[lo, hi], color=colors[i % len(colors)]))
    else:
        steps = [
            dict(range=[0, 0.15], color="#E8F5E9"),
            dict(range=[0.15, 0.25], color="#FFF3E0"),
            dict(range=[0.25, 1.0], color="#FFEBEE"),
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(size=14)),
        number=dict(font=dict(size=28)),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickwidth=1),
            bar=dict(color=APP_COLORS["primary"]),
            steps=steps,
            threshold=dict(
                line=dict(color="red", width=3),
                thickness=0.75,
                value=0.25,
            ),
        ),
    ))
    fig.update_layout(height=height, margin=dict(l=30, r=30, t=50, b=10))
    return fig


def create_treemap(
    df: pd.DataFrame,
    path: list[str],
    values: str,
    title: str,
    color: str | None = None,
    color_continuous_scale: str = "Viridis",
    height: int | None = None,
) -> go.Figure:
    """Create a treemap chart."""
    kwargs: dict = dict(path=path, values=values, title=title)
    if color:
        kwargs["color"] = color
        kwargs["color_continuous_scale"] = color_continuous_scale
    fig = px.treemap(df, **kwargs)
    fig.update_traces(textinfo="label+value+percent parent")
    return apply_common_layout(fig, height)


def create_heatmap(
    df_pivot: pd.DataFrame,
    title: str,
    x_label: str = "",
    y_label: str = "",
    color_scale: str = "YlOrRd",
    height: int | None = None,
) -> go.Figure:
    """Create a heatmap from a pivot table DataFrame."""
    fig = go.Figure(go.Heatmap(
        z=df_pivot.values,
        x=df_pivot.columns.tolist(),
        y=df_pivot.index.tolist(),
        colorscale=color_scale,
        text=np.round(df_pivot.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=10),
    ))
    fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label)
    return apply_common_layout(fig, height)


def create_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    size: str | None = None,
    hover_name: str | None = None,
    color_discrete_map: dict | None = None,
    color_continuous_scale: str | None = None,
    log_x: bool = False,
    log_y: bool = False,
    height: int | None = None,
) -> go.Figure:
    """Create a scatter plot."""
    fig = px.scatter(
        df, x=x, y=y, color=color, size=size,
        hover_name=hover_name, title=title,
        color_discrete_map=color_discrete_map,
        color_continuous_scale=color_continuous_scale,
        log_x=log_x, log_y=log_y,
    )
    return apply_common_layout(fig, height)


def create_waterfall(
    categories: list[str],
    values: list[float],
    title: str,
    height: int | None = None,
) -> go.Figure:
    """Create a waterfall chart for incremental changes."""
    measures = ["relative"] * len(values)
    measures[0] = "absolute"
    if len(measures) > 1:
        measures[-1] = "total"

    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=measures,
        connector=dict(line=dict(color="rgb(63, 63, 63)")),
        increasing=dict(marker=dict(color=APP_COLORS["positive"])),
        decreasing=dict(marker=dict(color=APP_COLORS["negative"])),
        totals=dict(marker=dict(color=APP_COLORS["primary"])),
        textposition="outside",
        text=[f"{v:+.1f}" for v in values],
    ))
    fig.update_layout(title=title, showlegend=False)
    return apply_common_layout(fig, height)


def create_forecast_chart(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    x: str,
    y_actual: str,
    y_forecast: str,
    title: str,
    y_lower: str | None = None,
    y_upper: str | None = None,
    height: int | None = None,
) -> go.Figure:
    """Create actual + forecast line with optional confidence band."""
    fig = go.Figure()

    if y_lower and y_upper and y_lower in forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast_df[x], forecast_df[x][::-1]]),
            y=pd.concat([forecast_df[y_upper], forecast_df[y_lower][::-1]]),
            fill="toself",
            fillcolor="rgba(108, 99, 255, 0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            name="95% CI", showlegend=True,
        ))

    fig.add_trace(go.Scatter(
        x=actual_df[x], y=actual_df[y_actual], name="Actual",
        line=dict(color="#1A73E8", width=2.5), mode="lines+markers",
    ))

    fig.add_trace(go.Scatter(
        x=forecast_df[x], y=forecast_df[y_forecast], name="Forecast",
        line=dict(color=APP_COLORS["primary"], width=2.5, dash="dash"),
        mode="lines+markers",
    ))

    if not actual_df.empty:
        last_actual = actual_df[x].max()
        fig.add_shape(
            type="line", x0=last_actual, x1=last_actual, y0=0, y1=1,
            yref="paper", line=dict(color="gray", width=1, dash="dot"),
        )
        fig.add_annotation(
            x=last_actual, y=1, yref="paper", text="Forecast →",
            showarrow=False, font=dict(size=10, color="gray"),
        )

    fig.update_layout(title=title, yaxis_title="Monthly Volume (Bn)")
    return apply_common_layout(fig, height)


def create_seasonal_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    height: int | None = None,
) -> go.Figure:
    """Create a seasonal factor bar chart with reference line at 1.0."""
    colors = [APP_COLORS["positive"] if v >= 1 else APP_COLORS["negative"]
              for v in df[y]]
    fig = go.Figure(go.Bar(
        x=df[x], y=df[y],
        marker_color=colors,
        text=[f"{v:.3f}" for v in df[y]],
        textposition="outside",
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray",
                  annotation_text="Baseline")
    fig.update_layout(title=title, yaxis_title="Seasonal Factor")
    return apply_common_layout(fig, height)
