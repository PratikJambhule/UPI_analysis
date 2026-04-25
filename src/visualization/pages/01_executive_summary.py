"""Tab 1: Executive Summary — KPIs, volume trends, category breakdown."""

import pandas as pd
import streamlit as st

from src.visualization.components.kpi_cards import (
    format_billions,
    format_lakh_crores,
    format_percentage,
    format_indian_rupee,
    render_kpi_row,
)
from src.visualization.components.charts import (
    create_bar_chart,
    create_line_chart,
    create_donut_chart,
    CATEGORY_COLORS,
    PLOTLY_CONFIG,
)
from src.visualization.components.styles import render_insight, render_divider, render_section_header


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Executive Summary tab."""
    render_section_header("Executive Summary — CXO Dashboard")

    required = ["fact_upi_transactions"]
    missing = [r for r in required if r not in data or data[r].empty]
    if missing:
        render_insight(
            f"Missing data: {', '.join(missing)}. Run <code>make all</code> first.",
            variant="warning",
        )
        return

    df = data["fact_upi_transactions"]
    df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    if df.empty:
        render_insight("No data available for the selected year range.")
        return

    #  KPI Cards (6 metrics) 
    total_txns = df["txn_count"].sum()
    total_value = df["txn_amount_inr"].sum()
    avg_txn = total_value / total_txns if total_txns > 0 else 0
    num_categories = df["category"].nunique()
    years_span = df["year"].max() - df["year"].min() + 1

    latest_year = df["year"].max()
    prev_year = latest_year - 1
    latest_txns = df[df["year"] == latest_year]["txn_count"].sum()
    prev_txns = df[df["year"] == prev_year]["txn_count"].sum()
    txn_growth = (latest_txns - prev_txns) / prev_txns if prev_txns > 0 else 0

    latest_value = df[df["year"] == latest_year]["txn_amount_inr"].sum()
    prev_value = df[df["year"] == prev_year]["txn_amount_inr"].sum()
    value_growth = (latest_value - prev_value) / prev_value if prev_value > 0 else 0

    latest_avg = latest_value / latest_txns if latest_txns > 0 else 0
    prev_avg = prev_value / prev_txns if prev_txns > 0 else 0
    avg_growth = (latest_avg - prev_avg) / prev_avg if prev_avg > 0 else 0

    # Row 1: 3 KPIs
    render_kpi_row([
        {"label": "Total Transactions", "value": format_billions(total_txns),
         "delta": f"{format_percentage(txn_growth)} YoY"},
        {"label": "Total Value Processed", "value": format_lakh_crores(total_value),
         "delta": f"{format_percentage(value_growth)} YoY"},
        {"label": "Avg Transaction Value", "value": format_indian_rupee(avg_txn),
         "delta": f"{format_percentage(avg_growth)} YoY", "delta_color": "inverse"},
    ])

    # Row 2: 3 more KPIs
    hhi_latest = None
    if "fact_market_concentration" in data and not data["fact_market_concentration"].empty:
        hhi_latest = data["fact_market_concentration"].iloc[-1]["hhi_index"]

    render_kpi_row([
        {"label": "Transaction Categories", "value": str(num_categories),
         "delta_color": "off"},
        {"label": "Years of Data", "value": f"{years_span} years",
         "delta": f"{df['year'].min()}–{df['year'].max()}", "delta_color": "off"},
        {"label": "Market HHI", "value": f"{hhi_latest:.4f}" if hhi_latest else "N/A",
         "delta": "Highly Concentrated" if hhi_latest and hhi_latest > 0.25 else "",
         "delta_color": "off"},
    ])

    render_divider()

    #  Yearly Volume + Value (side by side) 
    yearly = (
        df.groupby("year", as_index=False)
        .agg(total_txns=("txn_count", "sum"), total_value=("txn_amount_inr", "sum"))
    )
    yearly["txn_billions"] = yearly["total_txns"] / 1e9
    yearly["value_lakh_cr"] = yearly["total_value"] / 1e12

    col1, col2 = st.columns(2)

    with col1:
        fig_vol = create_bar_chart(
            yearly, x="year", y="txn_billions",
            title="Yearly Transaction Volume (Billions)",
            color_continuous_scale="Purples",
        )
        st.plotly_chart(fig_vol, width="stretch", config=PLOTLY_CONFIG)

    with col2:
        fig_val = create_bar_chart(
            yearly, x="year", y="value_lakh_cr",
            title="Yearly Transaction Value (₹ Lakh Crores)",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_val, width="stretch", config=PLOTLY_CONFIG)

    #  Monthly Trend + Category Breakdown (side by side) 
    col1, col2 = st.columns([3, 2])

    with col1:
        if "v_monthly_summary" in data and not data["v_monthly_summary"].empty:
            monthly = data["v_monthly_summary"].copy()
            monthly = monthly[
                (monthly["year"] >= year_range[0]) & (monthly["year"] <= year_range[1])
            ]
            monthly = monthly.sort_values(["year", "month"])
            monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
            monthly["txn_billions"] = monthly["total_transactions"] / 1e9

            fig_monthly = create_line_chart(
                monthly, x="period", y="txn_billions",
                title="Monthly Transaction Trend (Billions)",
                area_fill=True, markers=True,
            )
            st.plotly_chart(fig_monthly, width="stretch", config=PLOTLY_CONFIG)
        else:
            render_insight("Monthly summary data not available.")

    with col2:
        latest_cat = df[df["year"] == latest_year]
        if not latest_cat.empty and "category" in latest_cat.columns:
            cat_summary = latest_cat.groupby("category", as_index=False)["txn_count"].sum()
            # Map category codes to display names
            if "dim_category" in data:
                cat_map = dict(zip(
                    data["dim_category"]["category_code"],
                    data["dim_category"]["category_name"],
                ))
                cat_summary["category_name"] = cat_summary["category"].map(cat_map).fillna(cat_summary["category"])
            else:
                cat_summary["category_name"] = cat_summary["category"]

            fig_cat = create_donut_chart(
                cat_summary, values="txn_count", names="category_name",
                title=f"Transaction Categories ({latest_year})",
                color_discrete_map=CATEGORY_COLORS,
            )
            st.plotly_chart(fig_cat, width="stretch", config=PLOTLY_CONFIG)
        else:
            render_insight("Category breakdown data not available.")

    #  Year-over-Year Growth Table 
    if len(yearly) > 1:
        yearly["yoy_vol_growth"] = yearly["total_txns"].pct_change() * 100
        yearly["yoy_val_growth"] = yearly["total_value"].pct_change() * 100
        display_df = yearly[["year", "txn_billions", "value_lakh_cr", "yoy_vol_growth", "yoy_val_growth"]].copy()
        display_df.columns = ["Year", "Volume (Bn)", "Value (₹ LCr)", "Volume Growth %", "Value Growth %"]
        st.dataframe(
            display_df.style.format({
                "Volume (Bn)": "{:.2f}",
                "Value (₹ LCr)": "{:.2f}",
                "Volume Growth %": "{:+.1f}%",
                "Value Growth %": "{:+.1f}%",
            }, na_rep="—"),
            width="stretch", hide_index=True,
        )

    render_insight(
        f"<b>Key Takeaway:</b> India's UPI processed <b>{format_billions(total_txns)}</b> "
        f"transactions worth <b>{format_lakh_crores(total_value)}</b> between "
        f"{df['year'].min()}–{df['year'].max()}. "
        f"Transaction volumes grew <b>{format_percentage(txn_growth)}</b> YoY in {latest_year}, "
        f"while average transaction value {'declined' if avg_growth < 0 else 'grew'} "
        f"-- indicating {'more small-value payments are being made digitally' if avg_growth < 0 else 'adoption is growing for larger transactions'}."
    )
