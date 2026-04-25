"""Tests for chart builder functions."""

import pandas as pd
import plotly.graph_objects as go

from src.visualization.components.charts import (
    create_bar_chart,
    create_line_chart,
    create_donut_chart,
    create_dual_axis_chart,
    create_hhi_trend,
    create_forecast_chart,
    create_stacked_area,
    create_seasonal_bar,
    create_gauge,
    apply_common_layout,
    APP_COLORS,
)


def _sample_df():
    return pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30], "cat": ["a", "b", "c"]})


class TestApplyCommonLayout:
    def test_returns_figure(self):
        fig = go.Figure()
        result = apply_common_layout(fig)
        assert isinstance(result, go.Figure)

    def test_sets_template(self):
        fig = apply_common_layout(go.Figure())
        assert fig.layout.template.layout.to_plotly_json() is not None


class TestBarChart:
    def test_returns_figure(self):
        fig = create_bar_chart(_sample_df(), "x", "y", "Test")
        assert isinstance(fig, go.Figure)


class TestLineChart:
    def test_basic_line(self):
        fig = create_line_chart(_sample_df(), "x", "y", "Test")
        assert isinstance(fig, go.Figure)

    def test_area_fill(self):
        fig = create_line_chart(_sample_df(), "x", "y", "Test", area_fill=True)
        assert isinstance(fig, go.Figure)


class TestDonutChart:
    def test_returns_figure(self):
        fig = create_donut_chart(_sample_df(), "y", "cat", "Test")
        assert isinstance(fig, go.Figure)


class TestDualAxisChart:
    def test_returns_figure(self):
        df = pd.DataFrame({"x": [1, 2, 3], "y1": [10, 20, 30], "y2": [5, 15, 25]})
        fig = create_dual_axis_chart(df, "x", "y1", "y2", "Test")
        assert isinstance(fig, go.Figure)


class TestHHITrend:
    def test_returns_figure(self):
        df = pd.DataFrame({"period": ["2023-01", "2023-06"], "hhi": [0.37, 0.38]})
        fig = create_hhi_trend(df, "period", "hhi", "Test")
        assert isinstance(fig, go.Figure)


class TestForecastChart:
    def test_returns_figure(self):
        actual_df = pd.DataFrame({
            "ds": pd.date_range("2023-01", periods=3, freq="MS"),
            "actual": [1, 2, 3],
        })
        forecast_df = pd.DataFrame({
            "ds": pd.date_range("2023-04", periods=2, freq="MS"),
            "forecast": [4, 5],
            "lower": [3.5, 4.5],
            "upper": [4.5, 5.5],
        })
        fig = create_forecast_chart(actual_df, forecast_df, "ds", "actual", "forecast", "Test",
                                    y_lower="lower", y_upper="upper")
        assert isinstance(fig, go.Figure)


class TestStackedArea:
    def test_returns_figure(self):
        df = pd.DataFrame({
            "period": ["Jan", "Jan", "Feb", "Feb"],
            "share": [60, 40, 55, 45],
            "app": ["PhonePe", "GPay", "PhonePe", "GPay"],
        })
        fig = create_stacked_area(df, "period", "share", "app", "Test")
        assert isinstance(fig, go.Figure)


class TestSeasonalBar:
    def test_returns_figure(self):
        df = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar"],
            "factor": [1.05, 0.93, 1.01],
        })
        fig = create_seasonal_bar(df, "month", "factor", "Test")
        assert isinstance(fig, go.Figure)


class TestGauge:
    def test_returns_figure(self):
        fig = create_gauge(0.37, "HHI Index", max_val=0.5)
        assert isinstance(fig, go.Figure)


class TestAppColors:
    def test_has_major_apps(self):
        assert "PhonePe" in APP_COLORS
        assert "Google Pay" in APP_COLORS
        assert "Paytm" in APP_COLORS
