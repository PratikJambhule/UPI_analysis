"""
UPI Analytics Platform — Streamlit Web Application

Production-grade interactive dashboard analyzing India's UPI ecosystem.
Deployed on Streamlit Community Cloud.
"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

from src.visualization.components.data_loader import load_all_data, get_available_years
from src.visualization.components.styles import inject_custom_css, render_divider
from src.visualization.pages import (
    overview,
    executive_summary,
    growth_trends,
    market_share,
    app_dynamics,
    geographic_insights,
    district_deep_dive,
    cash_displacement,
    forecasting,
    users_devices,
    methodology,
)

#  Page Configuration 
st.set_page_config(
    page_title="UPI Analytics Platform",
    page_icon="bar_chart",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_css()

#  Data Loading 
data = load_all_data()

if not data:
    st.error(
        "**No data found.** The Gold layer exports are not available.\n\n"
        "Run the data pipeline first:\n"
        "```bash\n"
        "make all   # or: python -m src.pipeline.run_pipeline --stage all\n"
        "```"
    )
    st.stop()

#  Professional Header 
st.markdown(
    '<div class="dashboard-header">'
    '<h1 class="dashboard-title">UPI Analytics Platform</h1>'
    '<p class="dashboard-subtitle">'
    "Comprehensive Analysis of India's Digital Payments Ecosystem"
    "</p>"
    '<div class="header-badges">'
    '<span class="header-badge">3 Data Sources</span>'
    '<span class="header-badge">788 Districts</span>'
    '<span class="header-badge">42 Months</span>'
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

#  Filter Bar 
years = get_available_years(data)
col_spacer, col_filter = st.columns([4, 1])
with col_filter:
    year_range = st.slider(
        "Year Range",
        min_value=min(years),
        max_value=max(years),
        value=(min(years), max(years)),
        key="global_year_filter",
    )

render_divider()

#  Tab Navigation 
TAB_LABELS = [
    "Overview",
    "Executive Summary",
    "Growth & Trends",
    "Market Concentration",
    "App Dynamics",
    "Geographic Analysis",
    "District Deep Dive",
    "Cash vs Digital",
    "Forecasting",
    "Users & Devices",
    "Methodology",
]

TAB_PAGES = [
    overview,
    executive_summary,
    growth_trends,
    market_share,
    app_dynamics,
    geographic_insights,
    district_deep_dive,
    cash_displacement,
    forecasting,
    users_devices,
    methodology,
]

tabs = st.tabs(TAB_LABELS)

for tab, page in zip(tabs, TAB_PAGES):
    with tab:
        try:
            page.render(data, year_range)
        except Exception as e:
            st.error(f"Error rendering this section: {e}")
            import traceback
            st.code(traceback.format_exc(), language="text")
        render_divider()
        st.markdown(
            '<p class="footer-text">'
            'Made by <a href="https://github.com/PratikJambhule" target="_blank">Pratik Jambhule</a>'
            ' · <a href="https://github.com/PratikJambhule/UPI_analysis" target="_blank">GitHub Repository</a>'
            '</p>',
            unsafe_allow_html=True,
        )
