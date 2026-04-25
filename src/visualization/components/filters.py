"""Sidebar filter widget components."""

import streamlit as st
import pandas as pd


def render_year_filter(data: dict[str, pd.DataFrame], key: str = "year_filter") -> tuple[int, int]:
    """
    Render a year range slider in the sidebar.
    Returns (min_year, max_year) tuple.
    """
    if "fact_upi_transactions" in data and not data["fact_upi_transactions"].empty:
        years = sorted(data["fact_upi_transactions"]["year"].unique())
    else:
        years = list(range(2018, 2026))

    return st.slider(
        "Year Range",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years))),
        key=key,
    )


def render_state_filter(
    data: dict[str, pd.DataFrame],
    key: str = "state_filter",
    default_count: int = 5,
) -> list[str]:
    """
    Render a multi-select for states.
    Returns list of selected state names.
    """
    if "dim_geography" in data and not data["dim_geography"].empty:
        states = sorted(data["dim_geography"]["state_name"].unique())
    else:
        states = []

    if not states:
        return []

    return st.multiselect(
        "Select States",
        options=states,
        default=states[:default_count],
        key=key,
    )
