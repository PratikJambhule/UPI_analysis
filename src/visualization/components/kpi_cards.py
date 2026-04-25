"""Reusable KPI metric card components and number formatting utilities."""

import streamlit as st


def format_billions(value: float) -> str:
    """Format large numbers in billions: 15234567890 → '15.2 Bn'."""
    if abs(value) >= 1e9:
        return f"{value / 1e9:.1f} Bn"
    if abs(value) >= 1e6:
        return f"{value / 1e6:.1f} Mn"
    return f"{value:,.0f}"


def format_lakh_crores(value: float) -> str:
    """Format in Indian lakh crores: ₹20,00,00,00,00,000 → '₹20.0 LCr'."""
    lakh_cr = value / 1e12
    if abs(lakh_cr) >= 1:
        return f"₹{lakh_cr:.1f} LCr"
    # Fall back to crores
    crores = value / 1e7
    return f"₹{crores:.1f} Cr"


def format_crores(value: float) -> str:
    """Format in Indian crores."""
    return f"₹{value / 1e7:,.1f} Cr"


def format_percentage(value: float, with_sign: bool = True) -> str:
    """Format as percentage: 0.4623 → '+46.2%'."""
    if with_sign:
        return f"{value:+.1%}"
    return f"{value:.1%}"


def format_indian_rupee(value: float) -> str:
    """Format as Indian rupee with commas: 1374.5 → '₹1,375'."""
    return f"₹{value:,.0f}"


def render_kpi_row(metrics: list[dict]) -> None:
    """
    Render a row of KPI metric cards using st.columns + st.metric.

    Each dict in metrics should have:
        - label: str — metric title
        - value: str — formatted display value
        - delta: str (optional) — delta text (e.g., "+46% YoY")
        - delta_color: str (optional) — "normal", "inverse", or "off"
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            st.metric(
                label=metric["label"],
                value=metric["value"],
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "normal"),
            )
