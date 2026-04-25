"""Tab 3: Geographic Insights — Digital divide, state rankings, interactive maps."""

import pandas as pd
import streamlit as st

from src.visualization.components.kpi_cards import render_kpi_row, format_billions
from src.visualization.components.charts import (
    create_bar_chart,
    create_donut_chart,
    create_treemap,
    CLUSTER_COLORS,
    REGION_COLORS,
    PLOTLY_CONFIG,
)
from src.visualization.components.maps import (
    create_india_choropleth,
    create_india_bubble_map,
    create_choropleth_with_bubbles,
    create_district_heatmap_map,
    create_state_bar_map_fallback,
)
from src.visualization.components.styles import render_insight, render_divider, render_section_header


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Geographic Insights tab."""
    render_section_header("Geographic Analysis — State & District Level Insights")

    #  KPI Cards 
    num_states = 0
    num_districts = 0
    if "state_analysis" in data:
        num_states = len(data["state_analysis"])
    if "district_clusters" in data:
        num_districts = len(data["district_clusters"])

    underserved_count = 0
    if "underserved_districts" in data:
        underserved_count = len(data["underserved_districts"])

    avg_gini = 0
    if "state_analysis" in data and "intra_state_gini" in data["state_analysis"].columns:
        avg_gini = data["state_analysis"]["intra_state_gini"].mean()

    render_kpi_row([
        {"label": "States Analyzed", "value": str(num_states), "delta_color": "off"},
        {"label": "Districts Mapped", "value": f"{num_districts:,}", "delta_color": "off"},
        {"label": "Underserved Districts", "value": str(underserved_count),
         "delta": "Bottom 50 by adoption", "delta_color": "off"},
        {"label": "Avg State Gini", "value": f"{avg_gini:.3f}",
         "delta": "Intra-state inequality", "delta_color": "off"},
    ])

    render_divider()

    #  Interactive India Maps (Choropleth + Bubble side by side) 
    if "state_analysis" in data and not data["state_analysis"].empty:
        sa = data["state_analysis"].copy()
        sa["txn_billions"] = sa["total_transactions"] / 1e9
        sa["value_trillions"] = sa["total_value"] / 1e12

        map_metric = st.radio(
            "Select Map Metric",
            ["Transaction Volume (Bn)", "Transaction Value (₹ Trn)", "Avg Txn per District",
             "Intra-State Gini"],
            horizontal=True, key="geo_map_metric",
        )
        metric_map = {
            "Transaction Volume (Bn)": ("txn_billions", "YlOrRd"),
            "Transaction Value (₹ Trn)": ("value_trillions", "Purples"),
            "Avg Txn per District": ("avg_txn_per_district", "Blues"),
            "Intra-State Gini": ("intra_state_gini", "RdYlGn_r"),
        }
        color_col, scale = metric_map[map_metric]

        col_map1, col_map2 = st.columns(2)

        with col_map1:
            fig_choro = create_india_choropleth(
                sa, locations_col="state_clean", color_col=color_col,
                title=f" {map_metric} by State",
                color_scale=scale,
                hover_data=["num_districts", "intra_state_gini", "rank"],
                labels={
                    "txn_billions": "Txns (Bn)",
                    "value_trillions": "Value (₹ Trn)",
                    "avg_txn_per_district": "Avg Txn/District",
                    "intra_state_gini": "Gini",
                    "num_districts": "Districts",
                    "rank": "Rank",
                },
            )
            if fig_choro is not None:
                st.plotly_chart(fig_choro, width="stretch", config=PLOTLY_CONFIG)
            else:
                fig_fb = create_state_bar_map_fallback(
                    sa, state_col="state_clean", value_col=color_col,
                    title=f"Top 15 States — {map_metric}",
                )
                st.plotly_chart(fig_fb, width="stretch", config=PLOTLY_CONFIG)
                st.caption("Map will render when GeoJSON is available.")

        with col_map2:
            fig_bubble = create_india_bubble_map(
                sa, state_col="state_clean", size_col="txn_billions",
                color_col="intra_state_gini",
                title="Transaction Volume (size) × Gini (color)",
                hover_data=["num_districts", "rank"],
                color_scale="RdYlGn_r",
            )
            if fig_bubble is not None:
                st.plotly_chart(fig_bubble, width="stretch", config=PLOTLY_CONFIG)
            else:
                render_insight("Bubble map requires state coordinate data.")

    render_divider()

    #  State Rankings Table + Regional Breakdown 
    col1, col2 = st.columns([3, 2])

    with col1:
        if "v_state_rankings" in data and not data["v_state_rankings"].empty:
            rankings = data["v_state_rankings"].copy()
            rankings = rankings[
                (rankings["year"] >= year_range[0]) & (rankings["year"] <= year_range[1])
            ]
            state_agg = (
                rankings.groupby("state", as_index=False)
                .agg(
                    total_txns=("annual_transactions", "sum"),
                    total_value=("annual_value", "sum"),
                    num_districts=("num_districts", "max"),
                    pct_underserved=("pct_underserved_districts", "mean"),
                )
                .sort_values("total_txns", ascending=False)
            )
            state_agg.insert(0, "Rank", range(1, len(state_agg) + 1))
            state_agg["total_txns_bn"] = state_agg["total_txns"] / 1e9
            state_agg["pct_underserved"] = state_agg["pct_underserved"] * 100

            st.markdown("##### State Rankings by UPI Adoption")
            st.dataframe(
                state_agg[["Rank", "state", "total_txns_bn", "num_districts", "pct_underserved"]]
                .rename(columns={
                    "state": "State",
                    "total_txns_bn": "Txns (Bn)",
                    "num_districts": "Districts",
                    "pct_underserved": "% Underserved",
                }),
                width="stretch", hide_index=True, height=400,
                column_config={
                    "Txns (Bn)": st.column_config.NumberColumn(format="%.2f"),
                    "% Underserved": st.column_config.ProgressColumn(
                        min_value=0, max_value=100, format="%.1f%%",
                    ),
                },
            )

    with col2:
        if "dim_geography" in data and "state_analysis" in data:
            geo = data["dim_geography"][["state_name", "region"]].drop_duplicates("state_name")
            sa = data["state_analysis"].copy()
            merged = sa.merge(geo, left_on="state_clean", right_on="state_name", how="left")
            merged["region"] = merged["region"].fillna("Other")
            regional = merged.groupby("region", as_index=False)["total_transactions"].sum()

            fig_region = create_donut_chart(
                regional, values="total_transactions", names="region",
                title="Regional Distribution of UPI",
                color_discrete_map=REGION_COLORS,
            )
            st.plotly_chart(fig_region, width="stretch", config=PLOTLY_CONFIG)

    # Adoption tier treemap — full width below the columns
    if "district_clusters" in data and not data["district_clusters"].empty:
        dc = data["district_clusters"].copy()
        tier_state = (
            dc.groupby(["adoption_tier", "state_clean"], as_index=False)["total_txn"].sum()
            .sort_values("total_txn", ascending=False)
        )
        fig_tree = create_treemap(
            tier_state, path=["adoption_tier", "state_clean"],
            values="total_txn",
            title="Adoption Tier x State Treemap",
            color="total_txn",
            height=600,
        )
        fig_tree.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_tree, width="stretch", config=PLOTLY_CONFIG)

    #  District Drill-Down 
    render_divider()
    render_section_header("Interactive District Explorer")

    if "district_clusters" in data and not data["district_clusters"].empty:
        dc = data["district_clusters"].copy()
        states = sorted(dc["state_clean"].dropna().unique())

        selected_state = st.selectbox(
            "Select State to Explore Districts", states,
            key="geo_district_state",
        )

        if selected_state:
            state_districts = dc[dc["state_clean"] == selected_state].copy()
            n_districts = len(state_districts)
            total_txn = state_districts["total_txn"].sum()
            total_val = state_districts["total_value"].sum()

            # District KPIs for selected state
            render_kpi_row([
                {"label": f"Districts in {selected_state}", "value": str(n_districts),
                 "delta_color": "off"},
                {"label": "Total Transactions", "value": format_billions(total_txn),
                 "delta_color": "off"},
                {"label": "Total Value", "value": f"₹{total_val / 1e12:.2f}T",
                 "delta_color": "off"},
                {"label": "Avg per District", "value": format_billions(total_txn / max(n_districts, 1)),
                 "delta_color": "off"},
            ])

            col_d1, col_d2 = st.columns(2)

            with col_d1:
                fig_district = create_district_heatmap_map(
                    state_districts,
                    state_col="state_clean",
                    district_col="district_clean",
                    value_col="total_txn",
                    selected_state=selected_state,
                    title=f"Districts in {selected_state} — Transaction Volume",
                    height=450,
                )
                st.plotly_chart(fig_district, width="stretch", config=PLOTLY_CONFIG)

            with col_d2:
                # Adoption tier breakdown
                tier_counts = (
                    state_districts.groupby("adoption_tier", as_index=False)
                    .size()
                    .rename(columns={"size": "count"})
                )
                tier_order = ["Very Low Adoption", "Low Adoption", "Medium Adoption", "High Adoption"]
                tier_counts["adoption_tier"] = pd.Categorical(
                    tier_counts["adoption_tier"], categories=tier_order, ordered=True,
                )
                tier_counts = tier_counts.sort_values("adoption_tier")

                fig_tier = create_bar_chart(
                    tier_counts, x="adoption_tier", y="count",
                    title=f"Adoption Tiers in {selected_state}",
                    color="adoption_tier", color_discrete_map=CLUSTER_COLORS,
                    height=450,
                )
                st.plotly_chart(fig_tier, width="stretch", config=PLOTLY_CONFIG)

            # District detail table
            with st.expander(f"All {n_districts} Districts in {selected_state}", expanded=False):
                display_df = (
                    state_districts[["district_clean", "total_txn", "total_value",
                                     "avg_txn_value", "adoption_tier"]]
                    .sort_values("total_txn", ascending=False)
                    .rename(columns={
                        "district_clean": "District",
                        "total_txn": "Transactions",
                        "total_value": "Value (₹)",
                        "avg_txn_value": "Avg Txn (₹)",
                        "adoption_tier": "Adoption Tier",
                    })
                )
                st.dataframe(display_df, width="stretch", hide_index=True,
                             height=min(400, 35 * n_districts + 50))

    #  Cluster Distribution + Top/Bottom 
    render_divider()
    col1, col2 = st.columns(2)

    with col1:
        if "district_clusters" in data and not data["district_clusters"].empty:
            dc = data["district_clusters"].copy()
            cluster_counts = dc.groupby("adoption_tier", as_index=False).size()
            cluster_counts.columns = ["adoption_tier", "count"]
            tier_order = ["Very Low Adoption", "Low Adoption", "Medium Adoption", "High Adoption"]
            cluster_counts["adoption_tier"] = pd.Categorical(
                cluster_counts["adoption_tier"], categories=tier_order, ordered=True,
            )
            cluster_counts = cluster_counts.sort_values("adoption_tier")

            fig_cluster = create_bar_chart(
                cluster_counts, x="adoption_tier", y="count",
                title="All Districts by Adoption Tier",
                color="adoption_tier", color_discrete_map=CLUSTER_COLORS,
            )
            st.plotly_chart(fig_cluster, width="stretch", config=PLOTLY_CONFIG)

    with col2:
        if "fact_digital_divide" in data and not data["fact_digital_divide"].empty:
            dd = data["fact_digital_divide"].copy()
            dd["year"] = dd["date_key"] // 10000
            latest_year = dd["year"].max()
            latest_dd = dd[dd["year"] == latest_year]
            district_agg = (
                latest_dd.groupby(["state", "district"], as_index=False)
                .agg(total_txns=("total_txn_count", "sum"))
                .sort_values("total_txns", ascending=False)
            )

            top_tab, bottom_tab = st.tabs(["Top 10 Districts", "Bottom 10 Districts"])
            with top_tab:
                top_10 = district_agg.head(10).reset_index(drop=True)
                top_10.insert(0, "#", range(1, 11))
                st.dataframe(
                    top_10[["#", "state", "district", "total_txns"]].rename(columns={
                        "state": "State", "district": "District", "total_txns": "Transactions",
                    }),
                    width="stretch", hide_index=True,
                )
            with bottom_tab:
                bottom_10 = district_agg.tail(10).sort_values("total_txns").reset_index(drop=True)
                bottom_10.insert(0, "#", range(1, 11))
                st.dataframe(
                    bottom_10[["#", "state", "district", "total_txns"]].rename(columns={
                        "state": "State", "district": "District", "total_txns": "Transactions",
                    }),
                    width="stretch", hide_index=True,
                )

    render_insight(
        f"<b>Geographic Divide:</b> India's UPI adoption shows significant geographic disparity. "
        f"<b>{num_states}</b> states and <b>{num_districts}</b> districts analyzed reveal "
        f"<b>{underserved_count}</b> critically underserved districts. "
        f"The average intra-state Gini coefficient of <b>{avg_gini:.3f}</b> indicates substantial "
        f"inequality even within states — urban hubs dominate while rural districts lag behind. "
        f"Use the <b>District Explorer</b> above to drill down into any state's district-level data."
    )
