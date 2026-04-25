"""Tests for Phase 4 Analytics Engine modules."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


# ── HHI Analyzer ──────────────────────────────────────────────

class TestHHIAnalyzer:

    def test_import(self):
        from src.analytics.market_concentration import HHIAnalyzer
        analyzer = HHIAnalyzer()
        assert hasattr(analyzer, "run")

    def test_hhi_computation(self):
        from src.analytics.market_concentration import HHIAnalyzer
        analyzer = HHIAnalyzer()
        results = analyzer.compute_hhi_timeseries()
        assert len(results) == 13, f"Expected 13 periods, got {len(results)}"

    def test_hhi_values_in_range(self):
        from src.analytics.market_concentration import HHIAnalyzer
        analyzer = HHIAnalyzer()
        results = analyzer.compute_hhi_timeseries()
        for r in results:
            assert 0 < r.hhi <= 1.0, f"HHI {r.hhi} out of range"
            assert r.equivalent_firms >= 1.0
            assert 0 < r.top2_share <= 100

    def test_all_periods_highly_concentrated(self):
        from src.analytics.market_concentration import HHIAnalyzer
        analyzer = HHIAnalyzer()
        results = analyzer.compute_hhi_timeseries()
        for r in results:
            assert r.interpretation == "Highly Concentrated"

    def test_insights_generated(self):
        from src.analytics.market_concentration import HHIAnalyzer
        analyzer = HHIAnalyzer()
        results = analyzer.compute_hhi_timeseries()
        insights = analyzer.generate_insights(results)
        assert "key_findings" in insights
        assert len(insights["key_findings"]) >= 3

    def test_output_parquet_exists(self):
        output = Path("data/gold/exports/hhi_analysis.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) == 13
        assert "hhi" in df.columns
        assert "interpretation" in df.columns


# ── UPI Forecaster ────────────────────────────────────────────

class TestUPIForecaster:

    def test_import(self):
        from src.analytics.forecasting import UPIForecaster
        fc = UPIForecaster()
        assert fc.forecast_horizon == 12

    def test_arima_forecast_exists(self):
        output = Path("data/gold/exports/arima_forecast.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) == 12
        assert "arima_forecast_bn" in df.columns
        assert df["arima_forecast_bn"].notna().all()

    def test_arima_forecast_reasonable(self):
        df = pd.read_parquet("data/gold/exports/arima_forecast.parquet")
        # Forecasted volume should be > current (~18bn) and < 50bn
        assert df["arima_forecast_bn"].min() > 5.0
        assert df["arima_forecast_bn"].max() < 50.0

    def test_seasonal_factors_exist(self):
        output = Path("data/gold/exports/seasonal_factors.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) == 12
        assert "month" in df.columns
        assert "seasonal_factor" in df.columns

    def test_seasonal_factors_around_one(self):
        df = pd.read_parquet("data/gold/exports/seasonal_factors.parquet")
        mean_factor = df["seasonal_factor"].mean()
        assert 0.9 < mean_factor < 1.1, f"Mean seasonal factor {mean_factor} too far from 1.0"


# ── Digital Divide Analyzer ───────────────────────────────────

class TestDigitalDivideAnalyzer:

    def test_import(self):
        from src.analytics.geographic_analysis import DigitalDivideAnalyzer
        analyzer = DigitalDivideAnalyzer()
        assert hasattr(analyzer, "run")

    def test_state_analysis_exists(self):
        output = Path("data/gold/exports/state_analysis.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) >= 28  # At least 28 states
        assert "intra_state_gini" in df.columns
        assert "rank" in df.columns

    def test_gini_values_valid(self):
        df = pd.read_parquet("data/gold/exports/state_analysis.parquet")
        assert df["intra_state_gini"].between(0, 1).all()

    def test_district_clusters_exist(self):
        output = Path("data/gold/exports/district_clusters.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) >= 700
        assert set(df["adoption_tier"].unique()) == {
            "Very Low Adoption", "Low Adoption", "Medium Adoption", "High Adoption"
        }

    def test_underserved_districts(self):
        output = Path("data/gold/exports/underserved_districts.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) == 50
        # Should be sorted by total_txn ascending
        assert df["total_txn"].is_monotonic_increasing


# ── Cash Displacement Analyzer ────────────────────────────────

class TestCashDisplacementAnalyzer:

    def test_import(self):
        from src.analytics.cash_displacement import CashDisplacementAnalyzer
        analyzer = CashDisplacementAnalyzer()
        assert hasattr(analyzer, "run")

    def test_output_exists(self):
        output = Path("data/gold/exports/cash_displacement_analysis.parquet")
        assert output.exists()
        df = pd.read_parquet(output)
        assert len(df) == 34

    def test_displacement_velocity_computed(self):
        df = pd.read_parquet("data/gold/exports/cash_displacement_analysis.parquet")
        assert "displacement_velocity" in df.columns
        assert "velocity_pct" in df.columns
        assert "trend" in df.columns

    def test_ratio_increasing_overall(self):
        df = pd.read_parquet("data/gold/exports/cash_displacement_analysis.parquet")
        assert df.iloc[-1]["digital_to_cash_ratio"] > df.iloc[0]["digital_to_cash_ratio"]

    def test_trend_labels_valid(self):
        df = pd.read_parquet("data/gold/exports/cash_displacement_analysis.parquet")
        valid = {"Accelerating", "Decelerating", "Stable"}
        assert set(df["trend"].dropna().unique()).issubset(valid)


# ── Integration ───────────────────────────────────────────────

class TestAnalyticsIntegration:

    def test_all_analytics_outputs_exist(self):
        expected = [
            "hhi_analysis.parquet",
            "arima_forecast.parquet",
            "seasonal_factors.parquet",
            "state_analysis.parquet",
            "district_clusters.parquet",
            "underserved_districts.parquet",
            "cash_displacement_analysis.parquet",
        ]
        gold = Path("data/gold/exports")
        for f in expected:
            assert (gold / f).exists(), f"Missing: {f}"

    def test_full_pipeline_analytics_stage(self):
        from src.pipeline.orchestrator import PipelineOrchestrator
        orch = PipelineOrchestrator()
        assert orch._run_analytics() is True
