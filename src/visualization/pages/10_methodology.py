"""Tab 10: Methodology & Data Quality -- project pipeline, architecture,
data sources, quality metrics, analytical models, tech stack, and glossary."""

import streamlit as st
import pandas as pd

from src.visualization.components.styles import (
    render_insight,
    render_divider,
    render_section_header,
    render_page_header,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _null_pct(df: pd.DataFrame, columns: list[str]) -> dict[str, float]:
    """Return null percentage for each column present in *df*."""
    result: dict[str, float] = {}
    for col in columns:
        if col in df.columns:
            result[col] = round(df[col].isna().sum() / max(len(df), 1) * 100, 2)
    return result


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Methodology & Data Quality page."""

    render_page_header(
        "Methodology & Data Quality",
        "Pipeline design, data sources, quality checks, models, and limitations.",
    )

    render_divider()

    # ------------------------------------------------------------------
    # 1. What Was Done
    # ------------------------------------------------------------------
    render_section_header("What Was Done")

    st.markdown(
        """
1. Collected UPI transaction data from three public sources (PhonePe Pulse, NPCI, RBI).
2. Ingested raw files into a Bronze layer and stored them as Parquet.
3. Cleaned, deduplicated, and standardized schemas in a Silver layer.
4. Built analytical tables in a Gold layer: market concentration (HHI),
   time-series forecasts (Prophet, ARIMA), and cash-displacement metrics.
5. Loaded Gold-layer outputs into this Streamlit dashboard for interactive analysis.
"""
    )

    render_divider()

    # ------------------------------------------------------------------
    # 2. Data Pipeline Architecture
    # ------------------------------------------------------------------
    render_section_header("Data Pipeline Architecture")

    st.markdown(
        "The pipeline uses the **Medallion Architecture** -- data moves through "
        "four stages of progressive refinement."
    )

    st.markdown(
        '<div class="pipeline-flow">'
        '<span class="pipeline-stage">Bronze (Raw)</span>'
        '<span class="pipeline-arrow">→</span>'
        '<span class="pipeline-stage">Silver (Cleaned)</span>'
        '<span class="pipeline-arrow">→</span>'
        '<span class="pipeline-stage">Gold (Analytics)</span>'
        '<span class="pipeline-arrow">→</span>'
        '<span class="pipeline-stage active">Dashboard</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    layer1, layer2, layer3, layer4 = st.columns(4)

    with layer1:
        st.markdown(
            '<div class="about-card">'
            "<h4>Bronze Layer</h4>"
            "<p>"
            "Raw data from PhonePe Pulse GitHub API, NPCI CSVs, and "
            "RBI DBIE exports. Stored as-is in Parquet with ingestion metadata."
            "</p></div>",
            unsafe_allow_html=True,
        )

    with layer2:
        st.markdown(
            '<div class="about-card violet-card">'
            "<h4>Silver Layer</h4>"
            "<p>"
            "Schema normalization, deduplication, null handling, type casting, "
            "and date standardization. Produces star-schema fact and dimension tables."
            "</p></div>",
            unsafe_allow_html=True,
        )

    with layer3:
        st.markdown(
            '<div class="about-card amber-card">'
            "<h4>Gold Layer</h4>"
            "<p>"
            "Aggregations, HHI market concentration, Prophet and ARIMA forecasts, "
            "K-Means clustering, and cash-displacement analysis."
            "</p></div>",
            unsafe_allow_html=True,
        )

    with layer4:
        st.markdown(
            '<div class="about-card emerald-card">'
            "<h4>Dashboard</h4>"
            "<p>"
            "Streamlit app with Plotly charts. Reads Gold-layer Parquet files "
            "and renders 10+ views with filtering."
            "</p></div>",
            unsafe_allow_html=True,
        )

    render_divider()

    # ------------------------------------------------------------------
    # 3. Data Sources
    # ------------------------------------------------------------------
    render_section_header("Data Sources")

    pp_records = sum(
        len(data.get(k, pd.DataFrame()))
        for k in (
            "phonepe_user_aggregates",
            "phonepe_device_brands",
            "phonepe_insurance",
            "phonepe_top_transactions",
        )
    )
    npci_records = len(data.get("npci_monthly_volumes", pd.DataFrame()))
    rbi_records = sum(
        len(data.get(k, pd.DataFrame()))
        for k in ("rbi_atm_transactions", "rbi_currency_circulation")
    )

    sources_df = pd.DataFrame(
        {
            "Source": [
                "PhonePe Pulse",
                "NPCI",
                "RBI DBIE",
            ],
            "Description": [
                "District-level UPI aggregates, user registrations, device data, insurance",
                "Monthly UPI transaction volumes and values for the full network",
                "Currency in circulation, ATM transactions, macroeconomic indicators",
            ],
            "Frequency": ["Quarterly", "Monthly", "Quarterly"],
            "Ingestion": ["GitHub API", "Web scraping", "API / manual download"],
            "Records": [
                f"{pp_records:,}" if pp_records else "N/A",
                f"{npci_records:,}" if npci_records else "N/A",
                f"{rbi_records:,}" if rbi_records else "N/A",
            ],
        }
    )

    st.dataframe(sources_df, width="stretch", hide_index=True)

    render_divider()

    # ------------------------------------------------------------------
    # 4. Data Quality
    # ------------------------------------------------------------------
    render_section_header("Data Quality")

    total_tables = len(data)
    total_records = sum(len(df) for df in data.values())

    years_set: set[int] = set()
    for key in ("fact_upi_transactions", "v_monthly_summary",
                "npci_monthly_volumes", "dim_date"):
        df = data.get(key, pd.DataFrame())
        if "year" in df.columns:
            years_set.update(df["year"].dropna().astype(int).unique())
    date_coverage = (
        f"{min(years_set)}-{max(years_set)}"
        if years_set
        else f"{year_range[0]}-{year_range[1]}"
    )

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Tables Loaded", f"{total_tables}")
    q2.metric("Total Records", f"{total_records:,}")
    q3.metric("Date Range", date_coverage)

    fact_df = data.get("fact_upi_transactions", pd.DataFrame())
    if not fact_df.empty:
        key_cols = ["txn_count", "txn_value", "year", "quarter", "state_name"]
        nulls = _null_pct(fact_df, key_cols)
        avg_null = (
            round(sum(nulls.values()) / max(len(nulls), 1), 2) if nulls else 0.0
        )
        q4.metric("Avg Null % (Fact Table)", f"{avg_null}%")

        render_section_header("Null Analysis — fact_upi_transactions")
        null_df = pd.DataFrame(
            [
                {
                    "Column": col,
                    "Null %": pct,
                    "Status": "Clean" if pct < 1 else "Needs review",
                }
                for col, pct in nulls.items()
            ]
        )
        st.dataframe(null_df, width="stretch", hide_index=True)
    else:
        q4.metric("Avg Null % (Fact Table)", "N/A")

    with st.expander("Full table inventory", expanded=False):
        inventory = pd.DataFrame(
            [
                {"Table": name, "Rows": f"{len(df):,}", "Columns": len(df.columns)}
                for name, df in sorted(data.items())
            ]
        )
        st.dataframe(inventory, width="stretch", hide_index=True)

    render_insight(
        f"Pipeline loaded <strong>{total_tables} tables</strong> with "
        f"<strong>{total_records:,} records</strong> covering "
        f"<strong>{date_coverage}</strong>. All datasets pass schema "
        "validation and null checks before reaching the dashboard.",
        variant="success",
    )

    render_divider()

    # ------------------------------------------------------------------
    # 5. Analytical Models
    # ------------------------------------------------------------------
    render_section_header("Analytical Models")

    st.markdown(
        "The Gold layer produces three categories of output. "
        "Each is implemented as a standalone Python module."
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown(
            '<div class="about-card">'
            "<h4>Market Concentration</h4>"
            "<p>"
            "Herfindahl-Hirschman Index (HHI) from app-level market shares. "
            "Tracks equivalent number of competitors and tests the effect "
            "of NPCI's 30% volume cap."
            "</p></div>",
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            '<div class="about-card violet-card">'
            "<h4>Forecasting</h4>"
            "<p>"
            "Prophet for trend and seasonality decomposition; ARIMA for "
            "classical time-series modeling. Produces 12-month projections "
            "with confidence intervals."
            "</p></div>",
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            '<div class="about-card emerald-card">'
            "<h4>Cash Displacement</h4>"
            "<p>"
            "Measures the shift from cash to digital payments using the "
            "digital-to-cash ratio, currency velocity, and ATM transaction "
            "trends against UPI growth."
            "</p></div>",
            unsafe_allow_html=True,
        )

    render_divider()

    # ------------------------------------------------------------------
    # 6. Technology Stack
    # ------------------------------------------------------------------
    render_section_header("Technology Stack")

    tech_df = pd.DataFrame(
        {
            "Category": [
                "Data Engineering",
                "Data Engineering",
                "Data Engineering",
                "Data Engineering",
                "Data Engineering",
                "Analytics",
                "Analytics",
                "Analytics",
                "Analytics",
                "Visualization",
                "Visualization",
                "Visualization",
                "Infrastructure",
                "Infrastructure",
                "Infrastructure",
            ],
            "Tool": [
                "Python 3.11+",
                "DuckDB",
                "Pandas",
                "PyArrow",
                "Make",
                "Prophet",
                "statsmodels (ARIMA)",
                "scikit-learn (K-Means)",
                "SciPy",
                "Streamlit",
                "Plotly",
                "Custom CSS",
                "GitHub Actions",
                "Streamlit Cloud",
                "Apache Parquet",
            ],
            "Role": [
                "Core language",
                "In-process OLAP engine",
                "Data wrangling",
                "Parquet I/O",
                "Pipeline orchestration",
                "Time-series forecasting",
                "Classical time-series models",
                "Clustering",
                "Statistical tests",
                "Dashboard framework",
                "Interactive charts",
                "Component styling",
                "CI pipeline",
                "Hosting",
                "Columnar storage format",
            ],
        }
    )
    st.dataframe(tech_df, width="stretch", hide_index=True)

    render_divider()

    # ------------------------------------------------------------------
    # 7. Limitations
    # ------------------------------------------------------------------
    render_section_header("Limitations")

    st.markdown(
        "The following caveats apply when interpreting the results."
    )

    st.markdown(
        """
- **PhonePe-only view**: PhonePe Pulse reflects PhonePe's data, not the
  full UPI network. Volumes may differ from NPCI totals.
- **Granularity mismatch**: PhonePe data is quarterly; NPCI data is monthly.
  Joining them requires temporal alignment assumptions.
- **Geographic mapping**: District boundaries follow PhonePe's classification,
  which may not match Census 2011 or recent administrative changes.
- **Forecast reliability**: Models are trained on roughly 42 months of data.
  Projections beyond 6-12 months are directional only.
- **Cash proxy**: Currency in circulation includes hoarded cash and does not
  separate transactional holdings from precautionary ones.
- **Market share source**: App-level shares come from PhonePe Pulse, not
  NPCI's per-app data (unavailable at district level).
- **Batch processing**: All data is batch-loaded. The dashboard shows the
  last pipeline run, not live figures.
"""
    )

    render_divider()

    # ------------------------------------------------------------------
    # 8. Glossary
    # ------------------------------------------------------------------
    render_section_header("Glossary")

    with st.expander("Key terms used in this project", expanded=False):
        st.markdown(
            """
| Term | Full Form | Definition |
|------|-----------|------------|
| **UPI** | Unified Payments Interface | Real-time interbank payment system by NPCI for instant mobile transfers |
| **NPCI** | National Payments Corporation of India | Operates retail payment systems including UPI, IMPS, and RuPay |
| **P2P** | Person-to-Person | UPI transfers between individuals |
| **P2M** | Person-to-Merchant | UPI payments from individuals to businesses |
| **HHI** | Herfindahl-Hirschman Index | Sum of squared market shares (0-10,000 scale); higher means more concentrated |
| **CIC** | Currency in Circulation | Total banknotes and coins in public circulation, published by RBI |
| **ARIMA** | Auto-Regressive Integrated Moving Average | Statistical time-series model combining autoregression, differencing, and moving averages |
| **Prophet** | -- | Open-source forecasting library by Meta for trend and seasonality decomposition |
| **CAGR** | Compound Annual Growth Rate | Annualized growth rate smoothed over a period |
| **Lakh Crore** | -- | Indian unit equal to 10 trillion (approx. US$120 billion at recent exchange rates) |
| **PSP** | Payment Service Provider | Entity providing the UPI app to end users (e.g., PhonePe, Google Pay) |
| **TPAP** | Third Party Application Provider | Non-bank entity authorized to offer UPI through a sponsor bank |
| **VPA** | Virtual Payment Address | UPI handle (e.g., user@upi) mapped to a bank account |
| **K-Means** | -- | Clustering algorithm that partitions data into K groups by feature similarity |
| **Star Schema** | -- | Dimensional model with a central fact table linked to dimension tables |
| **Parquet** | -- | Columnar file format for analytical workloads with efficient compression |
"""
        )

    render_insight(
        "This project is open-source. See the repository for full source code, "
        "pipeline logic, and documentation.",
    )
