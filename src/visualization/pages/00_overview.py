"""Tab 0: Overview — Hero landing with project scale, key insights, and data sources."""

import streamlit as st
import pandas as pd

from src.visualization.components.styles import (
    render_insight,
    render_divider,
    render_scale_card,
    render_section_header,
)
from src.visualization.components.kpi_cards import (
    format_billions,
    format_lakh_crores,
    format_percentage,
)


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Overview / Hero landing tab."""

    # ── Hero Section ─────────────────────────────────────────────────
    st.markdown(
        '<div class="hero-title">UPI Analytics Platform</div>',
        unsafe_allow_html=True,
    )

    # Compute latest monthly volume from NPCI data
    npci = data.get("npci_monthly_volumes", pd.DataFrame())
    if "transaction_volume_billions" in npci.columns and not npci.empty:
        latest_monthly_vol = npci["transaction_volume_billions"].iloc[-1]
        hero_vol_text = f"{latest_monthly_vol:.0f} Bn+"
    else:
        hero_vol_text = "billions of"

    st.markdown(
        '<div class="hero-subtitle">'
        "A data engineering and analytics platform analyzing India's Unified Payments "
        f"Interface (UPI) — the world's largest real-time digital payment system, "
        f"processing {hero_vol_text} transactions per month."
        "</div>",
        unsafe_allow_html=True,
    )

    render_divider()

    # ── Key Insights (data-driven) ───────────────────────────────────
    render_section_header("Key Insights")
    _render_key_insights(data, year_range)

    render_divider()

    # ── Project Scale ────────────────────────────────────────────────
    render_section_header("Project Scale")

    total_data_points = sum(len(df) for df in data.values())

    geo = data.get("dim_geography", pd.DataFrame())
    n_states = geo["state_name"].nunique() if "state_name" in geo.columns else 36
    n_districts = geo["district_name"].nunique() if "district_name" in geo.columns else 788

    apps = data.get("dim_app", pd.DataFrame())
    n_apps = len(apps) if not apps.empty else 7

    years_set: set[int] = set()
    for key in ("fact_upi_transactions", "v_monthly_summary", "npci_monthly_volumes"):
        df = data.get(key, pd.DataFrame())
        if "year" in df.columns:
            years_set.update(df["year"].dropna().astype(int).unique())
    time_span = f"{min(years_set)}\u2013{max(years_set)}" if years_set else f"{year_range[0]}\u2013{year_range[1]}"

    if "transaction_volume_billions" in npci.columns and not npci.empty:
        total_vol = npci["transaction_volume_billions"].sum()
        vol_label = format_billions(total_vol * 1e9)
    else:
        fact = data.get("fact_upi_transactions", pd.DataFrame())
        total_vol = fact["txn_count"].sum() if "txn_count" in fact.columns else 0
        vol_label = format_billions(total_vol)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        render_scale_card(f"{total_data_points:,}", "Total Data Points")
    with col2:
        render_scale_card(str(n_states), "States & UTs", color="violet")
    with col3:
        render_scale_card(str(n_districts), "Districts Mapped", color="emerald")
    with col4:
        render_scale_card(str(n_apps), "UPI Apps Analyzed", color="amber")
    with col5:
        render_scale_card(time_span, "Time Span", color="rose")
    with col6:
        render_scale_card(vol_label, "Txn Volume Processed", color="cyan")

    st.markdown("")

    # ── About This Project ───────────────────────────────────────────
    render_section_header("About This Project")

    st.markdown(
        """
**UPI Analytics Platform** is an end-to-end data engineering and analytics project
that processes raw data from three public sources (PhonePe Pulse, NPCI, RBI),
transforms it through a Medallion Architecture pipeline (Bronze, Silver, Gold),
and produces the analytical datasets powering this dashboard.

The project covers market concentration analysis (HHI), time-series forecasting
(Prophet + ARIMA), geographic clustering (K-Means across 788 districts), and cash
displacement measurement -- applied to a payment system in a country of over 1.4 billion people.
""",
        unsafe_allow_html=True,
    )

    render_divider()

    # ── Why This Matters ─────────────────────────────────────────────
    render_section_header("Why This Matters")

    # Build text from actual data
    if "transaction_volume_billions" in npci.columns and not npci.empty:
        npci_sorted = npci.sort_values("date" if "date" in npci.columns else "year")
        latest_row = npci_sorted.iloc[-1]
        lv = latest_row["transaction_volume_billions"]
        lval = latest_row.get("transaction_value_lakh_crores", None)
        ldate = pd.to_datetime(latest_row["date"]).strftime("%b %Y") if "date" in latest_row.index else ""
        val_text = f" worth approx. {lval:.0f} Lakh Crore" if lval and lval > 0 else ""
        why_text = (
            f"<b>UPI processed {lv:.1f} Bn transactions{val_text} in {ldate}</b>. "
            "It is the largest real-time digital payment system in the world by "
            "transaction volume. India's digital payment infrastructure now handles "
            "the majority of retail transactions in the country. Analyzing this "
            "ecosystem provides direct insight into financial inclusion at national scale."
        )
    else:
        why_text = (
            "<b>UPI is the world's largest real-time digital payment system by volume.</b> "
            "Analyzing this ecosystem provides insight into financial inclusion at national scale."
        )

    render_insight(why_text)

    st.markdown("")

    # ── Data Sources ─────────────────────────────────────────────────
    render_section_header("Data Sources")

    src1, src2, src3 = st.columns(3)

    with src1:
        st.markdown(
            '<div class="about-card">'
            "<h4>PhonePe Pulse</h4>"
            "<p>"
            "Open-source dataset with district-level UPI adoption data, quarterly user "
            "registrations, and app-open metrics across all Indian states and districts."
            "</p>"
            '<p class="about-card-link">'
            '<a href="https://github.com/PhonePe/pulse" target="_blank">github.com/PhonePe/pulse</a>'
            "</p></div>",
            unsafe_allow_html=True,
        )

    with src2:
        st.markdown(
            '<div class="about-card violet-card">'
            "<h4>NPCI Statistics</h4>"
            "<p>"
            "Official monthly UPI transaction volumes and values published by the National "
            "Payments Corporation of India — the organization operating UPI."
            "</p>"
            '<p class="about-card-link">'
            '<a href="https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics" target="_blank">npci.org.in</a>'
            "</p></div>",
            unsafe_allow_html=True,
        )

    with src3:
        st.markdown(
            '<div class="about-card emerald-card">'
            "<h4>RBI DBIE</h4>"
            "<p>"
            "Reserve Bank of India's Database on Indian Economy — macroeconomic data "
            "including currency-in-circulation used for cash displacement analysis."
            "</p>"
            '<p class="about-card-link">'
            '<a href="https://dbie.rbi.org.in" target="_blank">dbie.rbi.org.in</a>'
            "</p></div>",
            unsafe_allow_html=True,
        )


def _render_key_insights(data: dict[str, pd.DataFrame], year_range: tuple) -> None:
    """Render data-driven key insights at the top of the overview."""

    insights = []

    # 1. Transaction scale
    fact = data.get("fact_upi_transactions", pd.DataFrame())
    if not fact.empty and "txn_count" in fact.columns:
        total_txns = fact["txn_count"].sum()
        total_value = fact["txn_amount_inr"].sum() if "txn_amount_inr" in fact.columns else 0
        latest_year = fact["year"].max()
        prev_year = latest_year - 1
        ly_txns = fact[fact["year"] == latest_year]["txn_count"].sum()
        py_txns = fact[fact["year"] == prev_year]["txn_count"].sum()
        yoy_growth = (ly_txns - py_txns) / py_txns if py_txns > 0 else 0
        insights.append(
            f"Total UPI transactions across all years: <b>{format_billions(total_txns)}</b> "
            f"worth <b>{format_lakh_crores(total_value)}</b>. "
            f"Volume grew <b>{format_percentage(yoy_growth)}</b> YoY in {latest_year}."
        )

    # 2. Market concentration
    conc = data.get("fact_market_concentration", pd.DataFrame())
    if not conc.empty and "hhi_index" in conc.columns:
        latest_hhi = conc.iloc[-1]["hhi_index"]
        top2 = conc.iloc[-1].get("top2_combined_share", 0)
        eq_firms = conc.iloc[-1].get("equivalent_firms", 0)
        insights.append(
            f"Market HHI: <b>{latest_hhi:.4f}</b> (Highly Concentrated by DOJ standards). "
            f"Top 2 apps control <b>~{top2:.0f}%</b> of transactions. "
            f"Effective competing firms: <b>{eq_firms:.1f}</b>."
        )

    # 3. Geographic divide
    clusters = data.get("district_clusters", pd.DataFrame())
    underserved = data.get("underserved_districts", pd.DataFrame())
    state_anal = data.get("state_analysis", pd.DataFrame())
    if not clusters.empty:
        n_districts = len(clusters)
        n_underserved = len(underserved) if not underserved.empty else 0
        avg_gini = state_anal["intra_state_gini"].mean() if not state_anal.empty and "intra_state_gini" in state_anal.columns else 0
        insights.append(
            f"<b>{n_districts}</b> districts analyzed. "
            f"<b>{n_underserved}</b> identified as critically underserved. "
            f"Average intra-state Gini: <b>{avg_gini:.3f}</b> — significant "
            f"inequality in UPI adoption within states."
        )

    # 4. Cash displacement
    cash = data.get("cash_displacement_analysis", pd.DataFrame())
    if not cash.empty and "digital_to_cash_ratio" in cash.columns:
        latest_ratio = cash["digital_to_cash_ratio"].iloc[-1]
        insights.append(
            f"Digital-to-cash ratio: <b>{latest_ratio:.2f}</b>. "
            "Currency in circulation continues to grow alongside UPI. "
            "India is becoming less cash-dependent, not cashless."
        )

    # 5. Forecast
    forecast = data.get("forecast_combined", pd.DataFrame())
    if not forecast.empty and "is_forecast" in forecast.columns:
        fcast = forecast[forecast["is_forecast"]]
        if not fcast.empty:
            final_vol = fcast["volume_bn"].iloc[-1]
            final_date = pd.to_datetime(fcast["date"].iloc[-1]).strftime("%b %Y")
            insights.append(
                f"Prophet + ARIMA models project monthly volumes reaching "
                f"<b>{final_vol:.1f} Bn</b> by <b>{final_date}</b>."
            )

    if insights:
        cols = st.columns(min(len(insights), 3))
        for i, text in enumerate(insights):
            with cols[i % len(cols)]:
                render_insight(text, variant="default")
    else:
        render_insight("Run the data pipeline to generate insights.")


