"""Tab 7: App Dynamics — Individual UPI app performance analysis."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.visualization.components.charts import (
    create_line_chart,
    create_horizontal_bar,
    create_stacked_area,
    APP_COLORS,
    PLOTLY_CONFIG,
    apply_common_layout,
)
from src.visualization.components.kpi_cards import render_kpi_row, format_percentage
from src.visualization.components.styles import (
    render_insight,
    render_divider,
    render_section_header,
    render_page_header,
)


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the App Dynamics tab."""
    render_page_header("App Dynamics")

    #  Validate data 
    if "app_market_share" not in data or data["app_market_share"].empty:
        render_insight(
            "App market share data not available. "
            "Run <code>make all</code> to build the data pipeline first.",
            variant="warning",
        )
        return

    df = data["app_market_share"].copy()

    #  Filter by year_range 
    if "year" in df.columns:
        df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    if df.empty:
        render_insight("No data available for the selected year range.")
        return

    df = df.sort_values(["year", "month"])
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    app_col = "app_name_clean" if "app_name_clean" in df.columns else "app_name"
    share_col = "market_share_pct" if "market_share_pct" in df.columns else "market_share"

    #  Latest snapshot 
    max_year = df["year"].max()
    latest_month_df = df[df["year"] == max_year]
    max_month = latest_month_df["month"].max()
    latest = latest_month_df[latest_month_df["month"] == max_month].copy()

    phonepe_share = latest.loc[latest[app_col] == "PhonePe", share_col]
    phonepe_val = phonepe_share.values[0] if not phonepe_share.empty else 0.0

    gpay_share = latest.loc[latest[app_col] == "Google Pay", share_col]
    gpay_val = gpay_share.values[0] if not gpay_share.empty else 0.0

    top2_val = phonepe_val + gpay_val
    num_active = latest[app_col].nunique()

    #  1. KPI Cards 
    render_kpi_row([
        {"label": "PhonePe (Leader)", "value": f"{phonepe_val:.1f}%", "delta_color": "off"},
        {"label": "Google Pay (#2)", "value": f"{gpay_val:.1f}%", "delta_color": "off"},
        {"label": "Top 2 Combined", "value": f"{top2_val:.1f}%", "delta_color": "off"},
        {"label": "Active Apps", "value": str(num_active), "delta_color": "off"},
    ])

    render_divider()

    #  2. Individual App Trajectory Lines 
    render_section_header("Individual App Trajectories")
    fig_lines = create_line_chart(
        df, x="period", y=share_col,
        title="Market Share Trajectory by App",
        color=app_col, color_discrete_map=APP_COLORS,
    )
    st.plotly_chart(fig_lines, width="stretch", config=PLOTLY_CONFIG)

    #  3 & 4: Horizontal Bar + Stacked Area side-by-side 
    col1, col2 = st.columns(2)

    with col1:
        render_section_header("Latest Market Share Snapshot")
        bar_df = latest.sort_values(share_col, ascending=True)
        fig_bar = create_horizontal_bar(
            bar_df, x=share_col, y=app_col,
            title=f"Market Share — {max_year}-{str(max_month).zfill(2)}",
            color=app_col, color_discrete_map=APP_COLORS,
        )
        fig_bar.add_vline(
            x=30, line_dash="dash", line_color=APP_COLORS["negative"], opacity=0.6,
            annotation_text="NPCI 30% Cap",
        )
        fig_bar.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=APP_COLORS["negative"], dash="dash"),
            name="NPCI 30% Cap", showlegend=True,
        ))
        st.plotly_chart(fig_bar, width="stretch", config=PLOTLY_CONFIG)

    with col2:
        render_section_header("Market Share Evolution (100% Stacked)")
        fig_area = create_stacked_area(
            df, x="period", y=share_col, color=app_col,
            title="Market Share Evolution Over Time",
            color_discrete_map=APP_COLORS,
        )
        st.plotly_chart(fig_area, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  5. Paytm Collapse Analysis 
    paytm_df = df[df[app_col] == "Paytm"].sort_values("period")
    if not paytm_df.empty and len(paytm_df) >= 2:
        paytm_peak = paytm_df[share_col].max()
        paytm_latest = paytm_df[share_col].iloc[-1]

        if paytm_peak > 0 and paytm_latest < paytm_peak * 0.7:
            render_section_header("Paytm Collapse Analysis")
            peak_row = paytm_df.loc[paytm_df[share_col].idxmax()]
            peak_period = peak_row["period"]
            latest_period = paytm_df["period"].iloc[-1]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Peak Share", f"{paytm_peak:.1f}%", delta=f"in {peak_period}", delta_color="off")
            with c2:
                st.metric("Current Share", f"{paytm_latest:.1f}%", delta=f"in {latest_period}", delta_color="off")
            with c3:
                decline = paytm_latest - paytm_peak
                st.metric("Decline", f"{decline:+.1f} pp",
                          delta=f"{decline / paytm_peak * 100:+.0f}% from peak", delta_color="inverse")

            fig_paytm = create_line_chart(
                paytm_df, x="period", y=share_col,
                title="Paytm Market Share Decline",
                markers=True,
            )
            fig_paytm.add_annotation(
                x=peak_period, y=paytm_peak,
                text=f"Peak: {paytm_peak:.1f}%",
                showarrow=True, arrowhead=2, ax=50, ay=-40,
                font=dict(size=11, color="#0f172a"),
                arrowcolor="#64748b",
            )
            st.plotly_chart(fig_paytm, width="stretch", config=PLOTLY_CONFIG)
            render_divider()

    #  6. App Comparison Table 
    render_section_header("App Comparison Table")
    table_df = latest[[app_col, share_col]].rename(
        columns={app_col: "App", share_col: "Market Share (%)"}
    ).sort_values("Market Share (%)", ascending=False).reset_index(drop=True)

    if "dim_app" in data and not data["dim_app"].empty:
        dim = data["dim_app"].copy()
        dim_name_col = "app_name" if "app_name" in dim.columns else dim.columns[1]
        dim = dim.rename(columns={dim_name_col: "App"})
        merge_cols = [c for c in dim.columns if c != "app_key"]
        table_df = table_df.merge(dim[merge_cols], on="App", how="left")

    st.dataframe(table_df, width="stretch", hide_index=True)

    render_divider()

    #  7. Duopoly Trend 
    if "fact_market_concentration" in data and not data["fact_market_concentration"].empty:
        render_section_header("Duopoly Trend — Top 2 Combined Share")
        conc = data["fact_market_concentration"].copy()
        conc["year"] = conc["date_key"] // 10000
        conc["month"] = (conc["date_key"] % 10000) // 100
        conc = conc[(conc["year"] >= year_range[0]) & (conc["year"] <= year_range[1])]
        conc = conc.sort_values(["year", "month"])
        conc["period"] = conc["year"].astype(str) + "-" + conc["month"].astype(str).str.zfill(2)

        if not conc.empty:
            fig_duo = create_line_chart(
                conc, x="period", y="top2_combined_share",
                title="Top 2 Combined Market Share Over Time",
                markers=True,
            )
            fig_duo.add_hline(
                y=60, line_dash="dash", line_color=APP_COLORS["warning"], opacity=0.5,
                annotation_text="60% Threshold",
            )
            fig_duo.add_trace(go.Scatter(
                x=[None], y=[None], mode="lines",
                line=dict(color=APP_COLORS["warning"], dash="dash"),
                name="60% Threshold", showlegend=True,
            ))
            st.plotly_chart(fig_duo, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  8. Insight Box 
    render_insight(
        "<b>Market Dynamics:</b> India's UPI ecosystem is dominated by a PhonePe-Google Pay "
        f"duopoly controlling <b>~{top2_val:.0f}%</b> of all transactions. "
        "Despite NPCI's proposed 30% volume cap, enforcement remains deferred. "
        "Paytm's sharp decline following RBI's action on Paytm Payments Bank has further "
        "consolidated the market. Newer entrants like CRED and WhatsApp Pay hold marginal share, "
        "highlighting the steep barriers to meaningful competition."
    )
