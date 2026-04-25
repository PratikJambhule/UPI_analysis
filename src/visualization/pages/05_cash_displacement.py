"""Tab 5: Cash Displacement — UPI vs cash analysis, ATM trends."""

import pandas as pd
import streamlit as st

from src.visualization.components.kpi_cards import (
    format_percentage,
    render_kpi_row,
)
from src.visualization.components.charts import (
    create_dual_axis_chart,
    create_line_chart,
    create_bar_chart,
    APP_COLORS,
    PLOTLY_CONFIG,
)
from src.visualization.components.styles import render_insight, render_divider, render_section_header


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Cash Displacement tab."""
    render_section_header("Cash vs Digital — Is India Going Cashless?")

    render_insight(
        "This analysis compares UPI transaction values against currency in circulation (CIC) "
        "to measure India's shift from cash to digital payments. A rising digital-to-cash ratio "
        "signals increasing digital adoption — but does not necessarily mean declining cash usage."
    )

    if "fact_cash_displacement" not in data or data["fact_cash_displacement"].empty:
        render_insight(
            "Cash displacement data not available. "
            "Run <code>make all</code> to build the data pipeline first.",
            variant="warning",
        )
        return

    df = data["fact_cash_displacement"].copy()
    df["year"] = df["date_key"] // 10000
    df["month"] = (df["date_key"] % 10000) // 100
    df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    if df.empty:
        render_insight("No data available for the selected year range.")
        return

    df = df.sort_values(["year", "month"])
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    #  KPI Cards 
    latest = df.iloc[-1]
    ratio = latest.get("digital_to_cash_ratio", 0)

    # YoY growth rates
    latest_year = df["year"].max()
    prev_year = latest_year - 1
    ly_upi = df[df["year"] == latest_year]["upi_value_lakh_cr"].mean()
    py_upi = df[df["year"] == prev_year]["upi_value_lakh_cr"].mean()
    upi_growth = (ly_upi - py_upi) / py_upi if py_upi and py_upi > 0 else 0

    ly_cic = df[df["year"] == latest_year]["cic_lakh_cr"].mean()
    py_cic = df[df["year"] == prev_year]["cic_lakh_cr"].mean()
    cic_growth = (ly_cic - py_cic) / py_cic if py_cic and py_cic > 0 else 0

    render_kpi_row([
        {"label": "Digital-to-Cash Ratio", "value": f"{ratio:.2f}",
         "delta_color": "off"},
        {"label": "UPI Value Growth", "value": format_percentage(upi_growth),
         "delta": "Year-over-Year", "delta_color": "off"},
        {"label": "Cash (CIC) Growth", "value": format_percentage(cic_growth),
         "delta": "Year-over-Year", "delta_color": "off"},
        {"label": "Verdict", "value": "Less Cash-Dependent",
         "delta": "NOT Cashless", "delta_color": "off"},
    ])

    render_divider()

    #  Dual-Axis Chart: UPI vs Cash 
    fig_dual = create_dual_axis_chart(
        df, x="period", y1="upi_value_lakh_cr", y2="cic_lakh_cr",
        title="UPI Transaction Value vs Currency in Circulation",
        y1_name="UPI Value (₹ Lakh Cr)", y2_name="Currency in Circulation (₹ Lakh Cr)",
        y1_color=APP_COLORS["primary"], y2_color=APP_COLORS["positive"],
    )
    st.plotly_chart(fig_dual, width="stretch", config=PLOTLY_CONFIG)

    #  Ratio Trend + Growth Comparison (side by side) 
    render_divider()
    col1, col2 = st.columns(2)

    with col1:
        fig_ratio = create_line_chart(
            df, x="period", y="digital_to_cash_ratio",
            title="Digital-to-Cash Ratio Trend",
            area_fill=True,
        )
        st.plotly_chart(fig_ratio, width="stretch", config=PLOTLY_CONFIG)

    with col2:
        yearly = df.groupby("year", as_index=False).agg(
            avg_upi=("upi_value_lakh_cr", "mean"),
            avg_cic=("cic_lakh_cr", "mean"),
        )
        yearly["upi_growth_pct"] = yearly["avg_upi"].pct_change() * 100
        yearly["cic_growth_pct"] = yearly["avg_cic"].pct_change() * 100
        yearly = yearly.dropna(subset=["upi_growth_pct"])

        if not yearly.empty:
            growth_melted = yearly.melt(
                id_vars=["year"],
                value_vars=["upi_growth_pct", "cic_growth_pct"],
                var_name="metric", value_name="growth_pct",
            )
            growth_melted["metric"] = growth_melted["metric"].map({
                "upi_growth_pct": "UPI Growth", "cic_growth_pct": "Cash Growth",
            })
            fig_growth = create_bar_chart(
                growth_melted, x="year", y="growth_pct",
                title="Annual Growth Rate Comparison (%)",
                color="metric",
                color_discrete_map={"UPI Growth": APP_COLORS["primary"], "Cash Growth": APP_COLORS["positive"]},
            )
            st.plotly_chart(fig_growth, width="stretch", config=PLOTLY_CONFIG)

    #  Velocity Analysis (if cash_displacement_analysis available) 
    if "cash_displacement_analysis" in data and not data["cash_displacement_analysis"].empty:
        cda = data["cash_displacement_analysis"].copy()
        cda["date"] = pd.to_datetime(cda["date"])
        cda = cda.sort_values("date")

        col1, col2 = st.columns(2)
        with col1:
            if "displacement_velocity" in cda.columns:
                vel_df = cda.dropna(subset=["displacement_velocity"])
                if not vel_df.empty:
                    fig_vel = create_line_chart(
                        vel_df, x="date", y="displacement_velocity",
                        title="Displacement Velocity",
                        markers=True,
                    )
                    st.plotly_chart(fig_vel, width="stretch", config=PLOTLY_CONFIG)

        with col2:
            if "trend" in cda.columns:
                trend_counts = cda["trend"].value_counts().reset_index()
                trend_counts.columns = ["trend", "count"]
                fig_trend = create_bar_chart(
                    trend_counts, x="trend", y="count",
                    title="Trend Classification Distribution",
                )
                st.plotly_chart(fig_trend, width="stretch", config=PLOTLY_CONFIG)

    #  ATM Transaction Comparison 
    if "rbi_atm_transactions" in data and not data["rbi_atm_transactions"].empty:
        render_divider()
        render_section_header("ATM Transaction Trends")
        atm = data["rbi_atm_transactions"].copy()
        atm["quarter_start_date"] = pd.to_datetime(atm["quarter_start_date"])
        atm = atm.sort_values("quarter_start_date")

        fig_atm = create_line_chart(
            atm, x="quarter_start_date", y="atm_transactions_millions",
            title="Quarterly ATM Transactions (Millions)",
            markers=True,
        )
        st.plotly_chart(fig_atm, width="stretch", config=PLOTLY_CONFIG)

    #  Insight Box 
    render_insight(
        "<b>Key Insight: India Is NOT Going Cashless</b> -- Despite UPI's rapid growth, "
        "currency in circulation continues to rise year-over-year. UPI is capturing "
        "<b>new transactions</b> (informal economy digitization -- street vendors, auto-rickshaws, "
        "small shops) rather than replacing existing cash usage. India is becoming "
        "<b>less cash-dependent</b>, not cashless. This distinction matters for "
        "policymakers and researchers studying digital payment adoption in emerging economies.",
        variant="warning",
    )
