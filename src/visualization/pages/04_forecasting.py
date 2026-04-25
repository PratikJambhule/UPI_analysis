"""Tab 4: Forecasting — Prophet/ARIMA projections and seasonal decomposition."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.visualization.components.kpi_cards import render_kpi_row
from src.visualization.components.charts import (
    apply_common_layout, APP_COLORS, PLOTLY_CONFIG,
    create_seasonal_bar,
)
from src.visualization.components.styles import render_insight, render_divider, render_section_header


def render(data: dict[str, pd.DataFrame], year_range: tuple[int, int]) -> None:
    """Render the Forecasting tab."""
    render_section_header("UPI Growth Forecasting — ML-Powered Projections")

    render_insight(
        "This section uses <b>Prophet</b> (additive decomposition by Meta) and "
        "<b>ARIMA</b> (classical auto-regressive) models to project UPI transaction volumes "
        "12 months ahead, with confidence intervals and seasonal factor analysis."
    )

    #  Check for forecast data 
    if "forecast_combined" not in data or data["forecast_combined"].empty:
        render_insight(
            "Forecast data not available. "
            "Run the analytics engine (<code>make analyze</code>) to generate forecasts.",
            variant="warning",
        )
        _show_placeholder()
        return

    forecast_df = data["forecast_combined"].copy()
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])
    forecast_df = forecast_df.sort_values("date")

    has_arima = "arima_forecast" in data and not data["arima_forecast"].empty
    has_seasonal = "seasonal_factors" in data and not data["seasonal_factors"].empty

    # Split actual vs forecast
    actual = forecast_df[~forecast_df["is_forecast"]]
    forecasted = forecast_df[forecast_df["is_forecast"]]

    #  KPI Cards 
    forecast_months = len(forecasted)
    latest_forecast = forecasted["volume_bn"].iloc[-1] if not forecasted.empty else 0

    # Find projected month for 25B milestone
    milestone_rows = forecasted[forecasted["volume_bn"] >= 25]
    milestone_date = milestone_rows["date"].min() if not milestone_rows.empty else None

    # Seasonal peak month
    if has_seasonal:
        sf = data["seasonal_factors"]
        peak_month_num = sf.loc[sf["seasonal_factor"].idxmax(), "month"]
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        peak_month = month_names[int(peak_month_num)] if 1 <= peak_month_num <= 12 else "N/A"
    else:
        peak_month = "November"

    render_kpi_row([
        {"label": "Forecast Horizon", "value": f"{forecast_months} months", "delta_color": "off"},
        {"label": "Projected 25B/month",
         "value": milestone_date.strftime("%b %Y") if milestone_date else "TBD",
         "delta_color": "off"},
        {"label": "Latest Forecast",
         "value": f"{latest_forecast:.1f} Bn",
         "delta_color": "off"},
        {"label": "Seasonal Peak", "value": f"{peak_month}", "delta_color": "off"},
    ])

    render_divider()

    #  Actual + Forecast Chart 
    fig = go.Figure()

    # ARIMA confidence interval band
    if has_arima:
        arima_df = data["arima_forecast"].copy()
        arima_df["date"] = pd.to_datetime(arima_df["date"])
        arima_df = arima_df.sort_values("date")

        fig.add_trace(go.Scatter(
            x=pd.concat([arima_df["date"], arima_df["date"][::-1]]),
            y=pd.concat([arima_df["arima_upper_bn"], arima_df["arima_lower_bn"][::-1]]),
            fill="toself",
            fillcolor="rgba(108, 99, 255, 0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            name="ARIMA 95% CI",
            showlegend=True,
        ))

    # Actual line
    fig.add_trace(go.Scatter(
        x=actual["date"], y=actual["volume_bn"],
        name="Actual", mode="lines+markers",
        line=dict(color=APP_COLORS["primary"], width=2.5),
        marker=dict(size=5),
    ))

    # Prophet/forecast line
    if not forecasted.empty:
        fig.add_trace(go.Scatter(
            x=forecasted["date"], y=forecasted["volume_bn"],
            name="Prophet Forecast", mode="lines+markers",
            line=dict(color=APP_COLORS["primary"], width=2.5, dash="dash"),
            marker=dict(size=5),
        ))

    # ARIMA line overlay
    if has_arima:
        fig.add_trace(go.Scatter(
            x=arima_df["date"], y=arima_df["arima_forecast_bn"],
            name="ARIMA Forecast", mode="lines",
            line=dict(color=APP_COLORS["warning"], width=2, dash="dot"),
        ))

    # Forecast start separator
    if not actual.empty:
        last_date = actual["date"].max()
        fig.add_shape(
            type="line", x0=last_date, x1=last_date, y0=0, y1=1,
            yref="paper", line=dict(color="gray", width=1, dash="dot"),
        )
        fig.add_annotation(
            x=last_date, y=1, yref="paper", text="Forecast Start ▸",
            showarrow=False, font=dict(size=10, color="#64748b"),
            xanchor="right", xshift=-6,
        )

    fig.update_layout(
        title="UPI Monthly Transaction Volume — Actual vs Forecast",
        yaxis_title="Monthly Transactions (Bn)",
        xaxis_title="",
    )
    st.plotly_chart(apply_common_layout(fig), width="stretch", config=PLOTLY_CONFIG)

    #  Seasonal Factors + ARIMA Details (side by side) 
    render_divider()
    col1, col2 = st.columns(2)

    with col1:
        if has_seasonal:
            sf = data["seasonal_factors"].copy()
            month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            sf["month_name"] = sf["month"].apply(
                lambda m: month_labels[int(m) - 1] if 1 <= m <= 12 else str(m)
            )

            fig_seasonal = create_seasonal_bar(
                sf, x="month_name", y="seasonal_factor",
                title="Monthly Seasonal Factors",
            )
            st.plotly_chart(fig_seasonal, width="stretch", config=PLOTLY_CONFIG)
        else:
            render_insight("Seasonal factor data not available.")

    with col2:
        if has_arima:
            render_section_header("ARIMA Forecast Details")
            arima_display = data["arima_forecast"].copy()
            arima_display["date"] = pd.to_datetime(arima_display["date"]).dt.strftime("%b %Y")
            arima_display.columns = ["Month", "Forecast (Bn)", "Lower CI", "Upper CI"]
            for c in ["Forecast (Bn)", "Lower CI", "Upper CI"]:
                arima_display[c] = arima_display[c].apply(lambda x: f"{x:.2f}")
            st.dataframe(arima_display, width="stretch", hide_index=True)

            render_section_header("Model Comparison")
            if not forecasted.empty and not arima_df.empty:
                prophet_end = forecasted["volume_bn"].iloc[-1]
                arima_end = arima_df["arima_forecast_bn"].iloc[-1]
                comparison = pd.DataFrame({
                    "Model": ["Prophet", "ARIMA"],
                    "Final Forecast (Bn)": [f"{prophet_end:.2f}", f"{arima_end:.2f}"],
                    "Method": ["Additive decomposition", "Auto-regressive"],
                })
                st.dataframe(comparison, width="stretch", hide_index=True)
        else:
            render_insight("ARIMA forecast data not available.")

    #  Forecast Insight 
    milestone_text = f"projected to reach <b>25 Bn/month</b> by <b>{milestone_date.strftime('%B %Y')}</b>" if milestone_date else "on track for continued growth"
    render_insight(
        f"<b>Forecast Insight:</b> Using Prophet (additive decomposition) and "
        f"ARIMA (auto-regressive) models trained on {len(actual)} months of data, "
        f"UPI transaction volumes are {milestone_text}. "
        f"Seasonal analysis reveals <b>{peak_month}</b> as the peak month, "
        f"driven by festival spending (Diwali, Dhanteras). "
        f"February consistently shows the lowest seasonal factor due to shorter month length.",
    )


def _show_placeholder() -> None:
    """Show placeholder content when forecast data isn't ready."""
    render_insight(
        "Once the analytics engine runs, this tab will display:<br>"
        "• <b>Prophet forecast</b> with confidence intervals<br>"
        "• <b>ARIMA comparison</b> forecast<br>"
        "• <b>Seasonal factors</b> by month",
    )
