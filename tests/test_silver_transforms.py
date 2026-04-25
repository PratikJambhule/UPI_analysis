"""Unit tests for Phase 2: Silver Layer transformations."""

import json
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SILVER = Path("data/silver")
REPORTS = SILVER / "quality_reports"


def _read(rel_path: str) -> pd.DataFrame:
    """Read a Silver parquet; skip test if missing."""
    p = SILVER / rel_path
    if not p.exists():
        pytest.skip(f"Silver file not found: {p}")
    return pd.read_parquet(p)


def _report(name: str) -> dict:
    """Read a JSON quality report."""
    p = REPORTS / name
    if not p.exists():
        pytest.skip(f"Report not found: {p}")
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# DataValidator report tests
# ---------------------------------------------------------------------------

class TestQualityReports:
    """All quality reports should exist and have PASSED status."""

    REPORT_FILES = [
        "phonepe_transactions.json",
        "district_transactions.json",
        "phonepe_users_agg.json",
        "phonepe_users_devices.json",
        "phonepe_insurance.json",
        "phonepe_top.json",
        "npci_volumes.json",
        "npci_market_share.json",
        "rbi_currency.json",
        "rbi_atm.json",
    ]

    @pytest.mark.parametrize("report_file", REPORT_FILES)
    def test_report_exists_and_passed(self, report_file):
        rpt = _report(report_file)
        assert rpt["status"] == "PASSED", f"{report_file} failed: {rpt}"


# ---------------------------------------------------------------------------
# PhonePe Transactions
# ---------------------------------------------------------------------------

class TestPhonePeTransactions:
    def test_row_count(self):
        df = _read("transactions/phonepe_agg_transactions.parquet")
        assert len(df) == 140

    def test_category_clean_populated(self):
        df = _read("transactions/phonepe_agg_transactions.parquet")
        assert df["category_clean"].notna().all()
        assert set(df["category_clean"]).issubset(
            {"recharge_bill_payments", "p2p_payments", "merchant_payments",
             "financial_services", "others"}
        )

    def test_has_derived_columns(self):
        df = _read("transactions/phonepe_agg_transactions.parquet")
        for col in ["quarter_start_date", "quarter_label", "avg_transaction_value", "is_p2m"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_no_negative_values(self):
        df = _read("transactions/phonepe_agg_transactions.parquet")
        assert (df["transaction_count"] >= 0).all()
        assert (df["transaction_amount"] >= 0).all()


# ---------------------------------------------------------------------------
# District Transactions
# ---------------------------------------------------------------------------

class TestDistrictTransactions:
    def test_row_count(self):
        df = _read("geographic/district_transactions.parquet")
        assert len(df) == 20604

    def test_state_clean_no_hyphens(self):
        df = _read("geographic/district_transactions.parquet")
        assert not df["state_clean"].str.contains("-").any()

    def test_district_clean_no_trailing_district(self):
        df = _read("geographic/district_transactions.parquet")
        assert not df["district_clean"].str.lower().str.endswith("district").any()

    def test_region_assigned(self):
        df = _read("geographic/district_transactions.parquet")
        assert df["region"].notna().all()
        assert "South" in df["region"].values

    def test_state_aggregation_exists(self):
        df = _read("geographic/state_transactions.parquet")
        assert len(df) > 0
        assert "state_clean" in df.columns
        assert "region" in df.columns


# ---------------------------------------------------------------------------
# PhonePe Users (split output)
# ---------------------------------------------------------------------------

class TestPhonePeUsers:
    def test_user_aggregates(self):
        df = _read("users/phonepe_user_aggregates.parquet")
        assert len(df) == 28
        assert df["registered_users"].notna().all()
        assert "device_brand" not in df.columns

    def test_device_brands(self):
        df = _read("users/phonepe_device_brands.parquet")
        assert len(df) == 187
        assert df["device_brand"].notna().all()
        assert "registered_users" not in df.columns


# ---------------------------------------------------------------------------
# NPCI Volumes
# ---------------------------------------------------------------------------

class TestNPCIVolumes:
    def test_row_count(self):
        df = _read("transactions/npci_monthly_volumes.parquet")
        assert len(df) == 42

    def test_fiscal_year_added(self):
        df = _read("transactions/npci_monthly_volumes.parquet")
        assert "fiscal_year" in df.columns
        assert df["fiscal_year"].str.startswith("FY").all()

    def test_fiscal_quarter_added(self):
        df = _read("transactions/npci_monthly_volumes.parquet")
        assert "fiscal_quarter" in df.columns
        assert set(df["fiscal_quarter"]).issubset({"Q1", "Q2", "Q3", "Q4"})


# ---------------------------------------------------------------------------
# NPCI Market Share
# ---------------------------------------------------------------------------

class TestNPCIMarketShare:
    def test_row_count(self):
        df = _read("market_share/app_market_share.parquet")
        assert len(df) == 91

    def test_top2_flag(self):
        df = _read("market_share/app_market_share.parquet")
        top2 = df[df["is_top2"]]
        assert set(top2["app_name_clean"]) == {"PhonePe", "Google Pay"}

    def test_parent_company_mapped(self):
        df = _read("market_share/app_market_share.parquet")
        assert "parent_company" in df.columns
        assert df["parent_company"].notna().all()


# ---------------------------------------------------------------------------
# RBI Currency in Circulation
# ---------------------------------------------------------------------------

class TestRBICurrency:
    def test_row_count(self):
        df = _read("transactions/rbi_currency_circulation.parquet")
        assert len(df) == 26

    def test_positive_values(self):
        df = _read("transactions/rbi_currency_circulation.parquet")
        assert (df["currency_in_circulation_lakh_cr"] > 0).all()


# ---------------------------------------------------------------------------
# RBI ATM Transactions
# ---------------------------------------------------------------------------

class TestRBIATM:
    def test_row_count(self):
        df = _read("transactions/rbi_atm_transactions.parquet")
        assert len(df) == 26

    def test_date_column_added(self):
        df = _read("transactions/rbi_atm_transactions.parquet")
        assert "quarter_start_date" in df.columns

    def test_positive_values(self):
        df = _read("transactions/rbi_atm_transactions.parquet")
        assert (df["atm_transactions_millions"] > 0).all()
