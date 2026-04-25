"""India choropleth and geographic map components using Plotly."""

import json
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.visualization.components.charts import apply_common_layout

#  State name normalization 
STATE_NAME_MAP = {
    "Andaman And Nicobar Islands": "Andaman & Nicobar Island",
    "Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Jammu And Kashmir": "Jammu & Kashmir",
    "Nct Of Delhi": "NCT of Delhi",
    "Delhi": "NCT of Delhi",
    "Telangana": "Telangana",
    "Ladakh": "Ladakh",
    "Lakshadweep": "Lakshadweep",
    "The Government Of Nct Of Delhi": "NCT of Delhi",
}

# Approximate state capital coordinates for bubble maps
STATE_COORDS: dict[str, tuple[float, float]] = {
    "Andhra Pradesh": (15.9129, 79.74),
    "Arunachal Pradesh": (28.218, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Goa": (15.2993, 74.124),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.467, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.533, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.855),
    "Andaman And Nicobar Islands": (11.7401, 92.6586),
    "Chandigarh": (30.7333, 76.7794),
    "Dadra And Nagar Haveli And Daman And Diu": (20.1809, 73.0169),
    "Jammu And Kashmir": (33.7782, 76.5762),
    "Ladakh": (34.1526, 77.5771),
    "Lakshadweep": (10.5667, 72.6417),
    "Nct Of Delhi": (28.7041, 77.1025),
    "Delhi": (28.7041, 77.1025),
    "Puducherry": (11.9416, 79.8083),
}


@st.cache_data(ttl=86400)
def load_india_geojson() -> dict | None:
    """Load India states GeoJSON — local file or public URL fallback."""
    local_paths = [
        Path("data/geojson/india_states.geojson"),
        Path("data/geojson/india_state_geo.geojson"),
    ]
    for p in local_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    try:
        import urllib.request
        url = (
            "https://gist.githubusercontent.com/jbrobst/"
            "56c13bbbf9d97d187fea01ca62ea5112/raw/"
            "e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
        )
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def normalize_state_name(name: str) -> str:
    """Normalize state name to match GeoJSON properties."""
    return STATE_NAME_MAP.get(name, name)


def _detect_feature_key(geojson: dict) -> str:
    """Auto-detect the GeoJSON property key for state names."""
    props = geojson["features"][0]["properties"]
    for key in ["ST_NM", "state", "NAME_1", "name", "NAME"]:
        if key in props:
            return f"properties.{key}"
    return f"properties.{list(props.keys())[0]}"


def _enrich_with_coords(df: pd.DataFrame, state_col: str) -> pd.DataFrame:
    """Add lat/lon columns based on state capital coordinates."""
    df = df.copy()
    df["_lat"] = df[state_col].map(lambda s: STATE_COORDS.get(s, (None, None))[0])
    df["_lon"] = df[state_col].map(lambda s: STATE_COORDS.get(s, (None, None))[1])
    return df.dropna(subset=["_lat", "_lon"])


def create_india_choropleth(
    df: pd.DataFrame,
    locations_col: str,
    color_col: str,
    title: str,
    color_scale: str = "YlOrRd",
    hover_data: list[str] | None = None,
    labels: dict[str, str] | None = None,
    height: int = 600,
) -> go.Figure | None:
    """Create an interactive India state-level choropleth map.

    Returns None if GeoJSON is unavailable.
    """
    geojson = load_india_geojson()
    if geojson is None:
        return None

    df = df.copy()
    df["_geo_state"] = df[locations_col].apply(normalize_state_name)

    feature_key = _detect_feature_key(geojson)

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="_geo_state",
        featureidkey=feature_key,
        color=color_col,
        color_continuous_scale=color_scale,
        title=title,
        hover_name=locations_col,
        hover_data=hover_data,
        labels=labels or {},
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(
            title=dict(text=color_col.replace("_", " ").title(), font=dict(size=12)),
            thickness=15,
            len=0.6,
        ),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_traces(
        marker_line_width=0.5,
        marker_line_color="white",
    )
    return apply_common_layout(fig, height)


def create_india_bubble_map(
    df: pd.DataFrame,
    state_col: str,
    size_col: str,
    color_col: str | None = None,
    title: str = "",
    hover_data: list[str] | None = None,
    color_scale: str = "Viridis",
    height: int = 600,
) -> go.Figure | None:
    """Create a scatter-geo bubble map of India using state capital coordinates.

    Automatically enriches the data with lat/lon from STATE_COORDS.
    Returns None if no states matched coordinates.
    """
    enriched = _enrich_with_coords(df, state_col)
    if enriched.empty:
        return None

    fig = px.scatter_geo(
        enriched,
        lat="_lat",
        lon="_lon",
        size=size_col,
        color=color_col or size_col,
        hover_name=state_col,
        hover_data=hover_data,
        title=title,
        color_continuous_scale=color_scale,
        size_max=40,
    )

    # Overlay on India choropleth outline
    geojson = load_india_geojson()
    if geojson is not None:
        feature_key = _detect_feature_key(geojson)
        # Create a transparent choropleth just for borders
        all_states = [f["properties"].get(feature_key.split(".")[-1], "")
                      for f in geojson["features"]]
        border_df = pd.DataFrame({"state": all_states, "val": [0] * len(all_states)})
        fig_border = px.choropleth(
            border_df, geojson=geojson, locations="state",
            featureidkey=feature_key, color="val",
            color_continuous_scale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        )
        fig_border.update_traces(
            marker_line_width=0.8, marker_line_color="rgba(150,150,150,0.5)",
            showlegend=False, showscale=False,
        )
        for trace in fig_border.data:
            fig.add_trace(trace)

    fig.update_geos(
        center=dict(lat=22.5, lon=82),
        projection_scale=4.5,
        visible=True,
        showland=True,
        landcolor="rgb(243, 243, 243)",
        showocean=True,
        oceancolor="rgb(230, 240, 255)",
        showcountries=True,
        countrycolor="rgb(200,200,200)",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=50, b=0),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return apply_common_layout(fig, height)


def create_choropleth_with_bubbles(
    choropleth_df: pd.DataFrame,
    bubble_df: pd.DataFrame,
    state_col: str,
    choro_color_col: str,
    bubble_size_col: str,
    title: str = "",
    choro_scale: str = "YlOrRd",
    height: int = 650,
) -> go.Figure | None:
    """Create a layered map: choropleth base + bubble overlay for dual metrics."""
    geojson = load_india_geojson()
    if geojson is None:
        return None

    choropleth_df = choropleth_df.copy()
    choropleth_df["_geo_state"] = choropleth_df[state_col].apply(normalize_state_name)
    feature_key = _detect_feature_key(geojson)

    fig = go.Figure()

    # Choropleth layer
    choro_fig = px.choropleth(
        choropleth_df, geojson=geojson, locations="_geo_state",
        featureidkey=feature_key, color=choro_color_col,
        color_continuous_scale=choro_scale, hover_name=state_col,
    )
    for trace in choro_fig.data:
        trace.marker.line.width = 0.5
        trace.marker.line.color = "white"
        fig.add_trace(trace)

    # Bubble layer
    enriched = _enrich_with_coords(bubble_df, state_col)
    if not enriched.empty:
        max_val = enriched[bubble_size_col].max()
        enriched["_size_scaled"] = (enriched[bubble_size_col] / max_val * 30).clip(lower=4)

        fig.add_trace(go.Scattergeo(
            lat=enriched["_lat"], lon=enriched["_lon"],
            text=enriched[state_col],
            marker=dict(
                size=enriched["_size_scaled"],
                color="rgba(26, 115, 232, 0.7)",
                line=dict(width=1, color="white"),
                sizemode="diameter",
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                + f"{bubble_size_col}: " + "%{customdata:.2f}<extra></extra>"
            ),
            customdata=enriched[bubble_size_col],
            name=bubble_size_col.replace("_", " ").title(),
            showlegend=True,
        ))

    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        title=title, height=height,
        margin=dict(l=0, r=0, t=50, b=0),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return apply_common_layout(fig, height)


def create_district_heatmap_map(
    district_df: pd.DataFrame,
    state_col: str,
    district_col: str,
    value_col: str,
    selected_state: str | None = None,
    title: str = "",
    height: int = 500,
) -> go.Figure:
    """Create a district-level heatmap bar chart for a selected state.

    Since district-level GeoJSON is impractical at runtime, this creates a
    visual bar-based heatmap sorted by value for district exploration.
    """
    df = district_df.copy()
    if selected_state:
        df = df[df[state_col] == selected_state]

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for selected state", showarrow=False, font=dict(size=16))
        return apply_common_layout(fig, height)

    df = df.sort_values(value_col, ascending=True)
    top_n = min(30, len(df))
    df = df.tail(top_n)

    fig = px.bar(
        df, x=value_col, y=district_col, orientation="h",
        color=value_col, color_continuous_scale="YlOrRd",
        title=title or f"District-Level {value_col.replace('_', ' ').title()}",
        hover_data=[state_col] if state_col in df.columns else None,
        text_auto=".2s",
    )
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending", tickfont=dict(size=10)),
        xaxis_title=value_col.replace("_", " ").title(),
        yaxis_title="",
        coloraxis_showscale=False,
    )
    fig.update_traces(textposition="outside", textfont_size=9)
    return apply_common_layout(fig, height)


def create_state_bar_map_fallback(
    df: pd.DataFrame,
    state_col: str,
    value_col: str,
    title: str,
    top_n: int = 15,
    height: int | None = None,
) -> go.Figure:
    """Fallback bar chart when GeoJSON is unavailable."""
    top = df.nlargest(top_n, value_col)
    fig = px.bar(
        top, x=value_col, y=state_col, orientation="h",
        title=title, text_auto=".2s",
        color=value_col, color_continuous_scale="YlOrRd",
    )
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    fig.update_traces(textposition="outside")
    return apply_common_layout(fig, height)
