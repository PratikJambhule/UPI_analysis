"""Tab 6: Growth & Trends — CAGR, volume trends, heatmaps, and festival impact."""

import streamlit as st
import pandas as pd
import numpy as np

from src.visualization.components.charts import (
    create_line_chart,
    create_bar_chart,
    create_heatmap,
    create_grouped_bar,
    APP_COLORS,
    PLOTLY_CONFIG,
    apply_common_layout,
)
from src.visualization.components.kpi_cards import (
    render_kpi_row,
    format_billions,
    format_percentage,
)
from src.visualization.components.styles import (
    render_insight,
    render_divider,
    render_section_header,
    render_page_header,
)

def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Growth & Trends tab."""
    render_page_header("Growth & Trends")

    required = ["npci_monthly_volumes"]
    missing = [r for r in required if r not in data or data[r].empty]
    if missing:
        render_insight(
            f"Missing data: {', '.join(missing)}. "
            "Run <code>make all</code> to build the data pipeline first.",
            variant="warning",
        )
        return

    #  Prepare NPCI monthly data 
    npci = data["npci_monthly_volumes"].copy()
    npci["date"] = pd.to_datetime(npci["date"])
    npci = npci[(npci["year"] >= year_range[0]) & (npci["year"] <= year_range[1])]
    npci = npci.sort_values("date")

    if npci.empty:
        render_insight("No data available for the selected year range.")
        return

    #  KPI Cards 
    latest_vol = npci["transaction_volume_billions"].iloc[-1]
    peak_vol = npci["transaction_volume_billions"].max()
    total_cumulative = npci["transaction_volume_billions"].sum()

    # CAGR: (end / start) ^ (1 / years) - 1
    first_vol = npci["transaction_volume_billions"].iloc[0]
    n_years = (npci["date"].iloc[-1] - npci["date"].iloc[0]).days / 365.25
    if first_vol > 0 and n_years > 0:
        cagr = (latest_vol / first_vol) ** (1 / n_years) - 1
    else:
        cagr = 0.0

    peak_row = npci.loc[npci["transaction_volume_billions"].idxmax()]
    peak_label = pd.to_datetime(peak_row["date"]).strftime("%b %Y")

    render_kpi_row([
        {"label": "CAGR (Volume)", "value": format_percentage(cagr, with_sign=False),
         "delta": "Compound Annual Growth", "delta_color": "off"},
        {"label": "Latest Monthly Volume", "value": format_billions(latest_vol * 1e9),
         "delta": npci["date"].iloc[-1].strftime("%b %Y"), "delta_color": "off"},
        {"label": "Peak Month Volume", "value": format_billions(peak_vol * 1e9),
         "delta": peak_label, "delta_color": "off"},
        {"label": "Total Cumulative Volume", "value": format_billions(total_cumulative * 1e9),
         "delta_color": "off"},
    ])

    render_divider()

    #  1. Monthly Volume Trend (Area) 
    render_section_header("Monthly Transaction Volume Trend")
    fig_volume = create_line_chart(
        npci, x="date", y="transaction_volume_billions",
        title="UPI Monthly Transaction Volume (Billions)",
        area_fill=True, markers=True,
    )
    st.plotly_chart(fig_volume, width="stretch", config=PLOTLY_CONFIG)

    #  2. YoY Growth Rate + 3. Heatmap (side by side) 
    col1, col2 = st.columns(2)

    with col1:
        render_section_header("Year-over-Year Growth Rate")
        yoy = npci[npci["yoy_volume_growth"].notna()].copy()
        if not yoy.empty:
            fig_yoy = create_line_chart(
                yoy, x="date", y="yoy_volume_growth",
                title="YoY Volume Growth (%)",
                area_fill=False, markers=True,
            )
            fig_yoy.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig_yoy, width="stretch", config=PLOTLY_CONFIG)
        else:
            render_insight("YoY growth data not available for the selected range.")

    with col2:
        render_section_header("Monthly Volume Heatmap")
        with st.spinner("Computing heatmap..."):
            month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            npci["month_name"] = npci["month"].apply(
                lambda m: month_labels[int(m) - 1] if 1 <= int(m) <= 12 else str(m)
            )
            pivot = npci.pivot_table(
                index="year", columns="month_name",
                values="transaction_volume_billions", aggfunc="mean",
            )
            # Reorder columns to Jan–Dec
            pivot = pivot.reindex(columns=[m for m in month_labels if m in pivot.columns])
            pivot.index = pivot.index.astype(int)

            fig_heat = create_heatmap(
                pivot,
                title="Volume Heatmap (Bn) — Month × Year",
                x_label="Month", y_label="Year",
            )
            st.plotly_chart(fig_heat, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  4. Quarterly Growth Bars 
    render_section_header("Quarterly Volume Breakdown")
    quarterly = (
        npci.groupby(["year", "fiscal_quarter"], as_index=False)
        ["transaction_volume_billions"].sum()
    )
    quarterly["year_str"] = quarterly["year"].astype(str)
    quarterly["quarter_label"] = quarterly["fiscal_quarter"].astype(str)
    if not quarterly["quarter_label"].str.startswith("Q").all():
        quarterly["quarter_label"] = "Q" + quarterly["quarter_label"]

    fig_qtr = create_grouped_bar(
        quarterly, x="quarter_label", y="transaction_volume_billions",
        color="year_str",
        title="Quarterly Transaction Volume by Year (Billions)",
    )
    st.plotly_chart(fig_qtr, width="stretch", config=PLOTLY_CONFIG)

    #  5. Average Transaction Value Trend 
    render_section_header("Average Transaction Value Trend")
    avg_txn = npci[npci["avg_transaction_value_inr"].notna()].copy()
    if not avg_txn.empty:
        fig_avg = create_line_chart(
            avg_txn, x="date", y="avg_transaction_value_inr",
            title="Average Transaction Value (₹) Over Time",
            area_fill=False, markers=True,
        )
        fig_avg.update_layout(yaxis_title="Avg Value (₹)")
        st.plotly_chart(fig_avg, width="stretch", config=PLOTLY_CONFIG)
    else:
        render_insight("Average transaction value data not available.")

    render_divider()

    #  6. Festival Impact Analysis 
    render_section_header("Festival Impact Analysis")
    if "v_monthly_summary" in data and not data["v_monthly_summary"].empty:
        monthly = data["v_monthly_summary"].copy()
        monthly = monthly[
            (monthly["year"] >= year_range[0]) & (monthly["year"] <= year_range[1])
        ]

        if "is_festival_month" in monthly.columns and not monthly.empty:
            festival = monthly[monthly["is_festival_month"] == 1]
            non_festival = monthly[monthly["is_festival_month"] == 0]

            fest_avg = festival["total_transactions"].mean() if not festival.empty else 0
            non_fest_avg = non_festival["total_transactions"].mean() if not non_festival.empty else 0
            fest_val_avg = festival["avg_transaction_value"].mean() if not festival.empty else 0
            non_fest_val_avg = non_festival["avg_transaction_value"].mean() if not non_festival.empty else 0

            col_a, col_b = st.columns(2)

            with col_a:
                comparison = pd.DataFrame({
                    "Category": ["Festival Months", "Non-Festival Months"],
                    "Avg Transactions": [fest_avg, non_fest_avg],
                })
                fig_fest = create_bar_chart(
                    comparison, x="Category", y="Avg Transactions",
                    title="Avg Monthly Transactions: Festival vs Non-Festival",
                )
                fig_fest.update_traces(marker_color=[APP_COLORS["warning"], APP_COLORS["primary"]])
                st.plotly_chart(fig_fest, width="stretch", config=PLOTLY_CONFIG)

            with col_b:
                val_comparison = pd.DataFrame({
                    "Category": ["Festival Months", "Non-Festival Months"],
                    "Avg Transaction Value (₹)": [fest_val_avg, non_fest_val_avg],
                })
                fig_val = create_bar_chart(
                    val_comparison, x="Category", y="Avg Transaction Value (₹)",
                    title="Avg Transaction Value: Festival vs Non-Festival",
                )
                fig_val.update_traces(marker_color=[APP_COLORS["warning"], APP_COLORS["primary"]])
                st.plotly_chart(fig_val, width="stretch", config=PLOTLY_CONFIG)

            # Festival month details
            if not festival.empty and "festival_name" in festival.columns:
                render_section_header("Festival Months in Data")
                fest_display = festival[["year", "month_name", "festival_name"]].copy()
                fest_display.columns = ["Year", "Month", "Festival"]
                st.dataframe(fest_display, width="stretch", hide_index=True)

            # Uplift percentage
            if non_fest_avg > 0:
                uplift = (fest_avg - non_fest_avg) / non_fest_avg
                uplift_text = (
                    f"Festival months show a <b>{uplift:+.1%}</b> uplift in average "
                    f"monthly transaction volume compared to non-festival months."
                )
            else:
                uplift_text = "Insufficient non-festival data for comparison."
        else:
            uplift_text = "Festival flag data not available in the monthly summary."
            render_insight(uplift_text)
    else:
        uplift_text = "Monthly summary data not available for festival analysis."
        render_insight(uplift_text)

    render_divider()

    #  7. Growth Narrative Insight 
    latest_date = npci["date"].iloc[-1].strftime("%B %Y")
    latest_yoy = npci["yoy_volume_growth"].dropna()
    latest_yoy_val = latest_yoy.iloc[-1] if not latest_yoy.empty else 0

    narrative = (
        f"<b>Growth Summary:</b> UPI transaction volumes have grown at a "
        f"<b>CAGR of {cagr:.1%}</b> over the selected period. "
        f"The latest monthly volume ({latest_date}) stands at <b>{latest_vol:.1f} Bn</b> "
        f"transactions, with a YoY growth rate of <b>{latest_yoy_val:.1%}</b>. "
        f"Peak volume of <b>{peak_vol:.1f} Bn</b> was recorded in <b>{peak_label}</b>. "
        f"Cumulative volume across the period totals <b>{total_cumulative:.1f} Bn</b> "
        f"transactions."
    )
    render_insight(narrative, variant="success")
