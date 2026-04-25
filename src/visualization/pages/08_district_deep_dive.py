"""Tab 8: District Deep Dive — Cluster analysis, inequality, and underserved districts."""

import pandas as pd
import streamlit as st

from src.visualization.components.charts import (
    create_bar_chart,
    create_scatter,
    create_treemap,
    create_horizontal_bar,
    CLUSTER_COLORS,
    PLOTLY_CONFIG,
    apply_common_layout,
)
from src.visualization.components.kpi_cards import render_kpi_row, format_billions
from src.visualization.components.styles import (
    render_insight,
    render_divider,
    render_section_header,
    render_page_header,
)

TIER_ORDER = ["Very Low Adoption", "Low Adoption", "Medium Adoption", "High Adoption"]


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the District-Level Deep Dive tab."""
    render_page_header("District-Level Deep Dive")

    render_insight(
        "Districts are grouped into <b>adoption tiers</b> using K-Means clustering on transaction "
        "volume and value. The Gini coefficient measures inequality in UPI adoption within each state."
    )

    clusters = data.get("district_clusters", pd.DataFrame())
    underserved = data.get("underserved_districts", pd.DataFrame())
    state_anal = data.get("state_analysis", pd.DataFrame())
    digital_divide = data.get("fact_digital_divide", pd.DataFrame())
    geography = data.get("dim_geography", pd.DataFrame())

    if clusters.empty:
        render_insight(
            "District cluster data not available. "
            "Run <code>make all</code> to build the data pipeline first.",
            variant="warning",
        )
        return

    #  KPI Cards 
    total_districts = len(clusters)
    num_underserved = len(underserved) if not underserved.empty else 0
    avg_gini = (
        f"{state_anal['intra_state_gini'].mean():.3f}"
        if not state_anal.empty and "intra_state_gini" in state_anal.columns
        else "N/A"
    )
    num_clusters = (
        clusters["adoption_tier"].nunique()
        if "adoption_tier" in clusters.columns
        else 0
    )

    render_kpi_row([
        {"label": "Total Districts Analyzed", "value": f"{total_districts:,}", "delta_color": "off"},
        {"label": "Underserved Districts", "value": str(num_underserved),
         "delta": "Bottom 50 by txn count", "delta_color": "off"},
        {"label": "Avg Gini Coefficient", "value": avg_gini,
         "delta": "Across states", "delta_color": "off"},
        {"label": "Adoption Tiers", "value": str(num_clusters), "delta_color": "off"},
    ])

    render_divider()

    #  1. Cluster Distribution Bar 
    render_section_header("Cluster Distribution")

    cluster_counts = (
        clusters.groupby("adoption_tier", as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    cluster_counts["adoption_tier"] = pd.Categorical(
        cluster_counts["adoption_tier"], categories=TIER_ORDER, ordered=True,
    )
    cluster_counts = cluster_counts.sort_values("adoption_tier")

    fig_cluster = create_bar_chart(
        cluster_counts,
        x="adoption_tier",
        y="count",
        title="Number of Districts per Adoption Tier",
        color="adoption_tier",
        color_discrete_map=CLUSTER_COLORS,
    )
    st.plotly_chart(fig_cluster, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  2. District Scatter Plot 
    render_section_header("District Transaction Landscape")

    with st.spinner("Rendering district scatter plot..."):
        fig_scatter = create_scatter(
            clusters,
            x="total_txn",
            y="avg_txn_value",
            title="District Transactions vs Avg Transaction Value",
            color="adoption_tier",
            size="total_value",
            hover_name="district_clean",
            color_discrete_map=CLUSTER_COLORS,
            log_x=True,
        )
    st.plotly_chart(fig_scatter, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  3. Top 10 vs Bottom 10 Districts 
    render_section_header("Top 10 vs Bottom 10 Districts")

    sorted_districts = clusters.sort_values("total_txn", ascending=False)
    top_10 = sorted_districts.head(10)[["district_clean", "state_clean", "total_txn"]].reset_index(drop=True)
    bottom_10 = sorted_districts.tail(10).sort_values("total_txn")[["district_clean", "state_clean", "total_txn"]].reset_index(drop=True)

    col_top, col_bottom = st.columns(2)

    with col_top:
        render_section_header("Top 10 Districts")
        st.dataframe(
            top_10.rename(columns={
                "district_clean": "District",
                "state_clean": "State",
                "total_txn": "Total Transactions",
            }),
            width="stretch",
            hide_index=True,
        )

    with col_bottom:
        render_section_header("Bottom 10 Districts")
        st.dataframe(
            bottom_10.rename(columns={
                "district_clean": "District",
                "state_clean": "State",
                "total_txn": "Total Transactions",
            }),
            width="stretch",
            hide_index=True,
        )

    render_divider()

    #  4. State-level Gini Inequality 
    if not state_anal.empty and "intra_state_gini" in state_anal.columns:
        render_section_header("State-level Gini Inequality")

        gini_df = (
            state_anal[["state_clean", "intra_state_gini"]]
            .sort_values("intra_state_gini", ascending=True)
            .copy()
        )

        fig_gini = create_horizontal_bar(
            gini_df,
            x="intra_state_gini",
            y="state_clean",
            title="Intra-State Gini Coefficient (Higher = More Inequality)",
        )
        fig_gini.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig_gini, width="stretch", config=PLOTLY_CONFIG)

        render_divider()

    #  5. Underserved Districts Table 
    if not underserved.empty:
        render_section_header("Underserved Districts")
        st.caption("Bottom 50 districts by transaction count — potential targets for financial inclusion programs.")

        st.dataframe(
            underserved[["state_clean", "district_clean", "total_txn"]]
            .rename(columns={
                "state_clean": "State",
                "district_clean": "District",
                "total_txn": "Total Transactions",
            }),
            width="stretch",
            hide_index=True,
            height=400,
        )

        render_divider()

    #  6. Adoption Tier Treemap 
    render_section_header("Adoption Tier Treemap")

    with st.spinner("Building treemap..."):
        treemap_df = clusters[["adoption_tier", "state_clean", "total_txn"]].copy()
        treemap_df = treemap_df.dropna(subset=["adoption_tier", "state_clean", "total_txn"])

        fig_treemap = create_treemap(
            treemap_df,
            path=["adoption_tier", "state_clean"],
            values="total_txn",
            title="District Transactions by Adoption Tier & State",
            color="total_txn",
            height=600,
        )
        fig_treemap.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_treemap, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  7. District Distribution by State 
    render_section_header("District Distribution by State")

    states = sorted(clusters["state_clean"].dropna().unique())
    selected_state = st.selectbox("Select a State", states, key="district_deep_dive_state")

    if selected_state:
        state_df = clusters[clusters["state_clean"] == selected_state]
        state_tier_counts = (
            state_df.groupby("adoption_tier", as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        state_tier_counts["adoption_tier"] = pd.Categorical(
            state_tier_counts["adoption_tier"], categories=TIER_ORDER, ordered=True,
        )
        state_tier_counts = state_tier_counts.sort_values("adoption_tier")

        fig_state = create_bar_chart(
            state_tier_counts,
            x="adoption_tier",
            y="count",
            title=f"Adoption Tier Distribution — {selected_state}",
            color="adoption_tier",
            color_discrete_map=CLUSTER_COLORS,
        )
        st.plotly_chart(fig_state, width="stretch", config=PLOTLY_CONFIG)

    render_divider()

    #  Insight Box 
    render_insight(
        "**Digital Divide Insight:** India's UPI adoption shows significant geographic "
        "disparity. A small number of urban districts dominate transaction volumes while "
        "the bottom 50 districts contribute a negligible share. High intra-state Gini "
        "coefficients reveal that inequality exists not just between states but within "
        "them — targeted financial inclusion programs should focus on these underserved "
        "pockets to bridge the digital divide."
    )
