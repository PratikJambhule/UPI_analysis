"""Silver Layer Transformer — Cleans and standardizes Bronze data."""

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from src.transformation.data_validator import DataValidator


class SilverTransformer:
    """Transforms Bronze (raw) → Silver (clean, validated, standardized)."""

    def __init__(self):
        self.bronze = Path("data/bronze")
        self.silver = Path("data/silver")
        self.reports = Path("data/silver/quality_reports")
        self.silver.mkdir(parents=True, exist_ok=True)
        self.reports.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        """Execute all transformations. Returns True if all succeed."""
        results = [
            self._transform_phonepe_transactions(),
            self._transform_phonepe_districts(),
            self._transform_phonepe_users(),
            self._transform_phonepe_insurance(),
            self._transform_phonepe_top(),
            self._transform_npci_volumes(),
            self._transform_npci_market_share(),
            self._transform_rbi_currency(),
            self._transform_rbi_atm(),
        ]
        passed = sum(results)
        total = len(results)
        logger.info(f"Silver layer: {passed}/{total} transforms succeeded")
        return all(results)

    # ── PhonePe Transactions (country-level) ─────────────────────────

    def _transform_phonepe_transactions(self) -> bool:
        """Clean PhonePe country-level aggregated transactions."""
        src = self.bronze / "phonepe_pulse" / "agg_transactions_country.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)

        # Standardize category names
        cat_map = {
            "Recharge & bill payments": "recharge_bill_payments",
            "Peer-to-peer payments": "p2p_payments",
            "Merchant payments": "merchant_payments",
            "Financial Services": "financial_services",
            "Others": "others",
        }
        df["category_clean"] = df["category"].map(cat_map).fillna(
            df["category"].str.lower().str.replace(" ", "_").str.replace("&", "and")
        )

        # P2P vs P2M flag
        df["is_p2m"] = df["category_clean"].isin(["merchant_payments", "recharge_bill_payments"])

        # Date columns
        df["quarter_start_date"] = pd.to_datetime(
            df.apply(lambda r: f"{r['year']}-{(r['quarter']-1)*3 + 1:02d}-01", axis=1)
        )
        df["quarter_label"] = df.apply(lambda r: f"Q{r['quarter']} {r['year']}", axis=1)

        # Type enforcement
        df["transaction_count"] = df["transaction_count"].astype(np.int64)
        df["transaction_amount"] = df["transaction_amount"].astype(np.float64)

        # Derived metric
        df["avg_transaction_value"] = np.where(
            df["transaction_count"] > 0,
            df["transaction_amount"] / df["transaction_count"],
            0.0,
        )

        # Drop ingestion metadata
        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        # Validate
        ok = (
            DataValidator(df, "PhonePe Transactions")
            .check_not_empty()
            .check_no_nulls(["year", "quarter", "transaction_count", "transaction_amount"])
            .check_positive_values(["transaction_count", "transaction_amount"])
            .check_no_duplicates(["year", "quarter", "category", "instrument_type"])
            .report(self.reports / "phonepe_transactions.json")
        )
        if not ok:
            return False

        out = self.silver / "transactions" / "phonepe_agg_transactions.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} PhonePe transaction records → {out}")
        return True

    # ── PhonePe Districts ────────────────────────────────────────────

    def _transform_phonepe_districts(self) -> bool:
        """Clean district-level transaction data — the most valuable dataset."""
        src = self.bronze / "phonepe_pulse" / "map_transactions_district.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)

        # Standardize state names (PhonePe uses lowercase-hyphenated)
        df["state_clean"] = (
            df["state"].str.replace("-", " ").str.title().str.strip()
        )
        state_fixes = {
            "Andaman & Nicobar Islands": "Andaman And Nicobar Islands",
            "Dadra & Nagar Haveli & Daman & Diu": "Dadra And Nagar Haveli And Daman And Diu",
            "Jammu & Kashmir": "Jammu And Kashmir",
        }
        df["state_clean"] = df["state_clean"].replace(state_fixes)

        # Standardize district names (remove trailing " district", title case)
        df["district_clean"] = (
            df["district"]
            .str.strip()
            .str.replace(r"\s*district\s*$", "", regex=True, case=False)
            .str.title()
            .str.replace(r"\s+", " ", regex=True)
        )

        # Region classification
        region_map = {
            "Maharashtra": "West", "Gujarat": "West", "Rajasthan": "West", "Goa": "West",
            "Uttar Pradesh": "North", "Delhi": "North", "Haryana": "North", "Punjab": "North",
            "Himachal Pradesh": "North", "Uttarakhand": "North", "Chandigarh": "North",
            "Jammu And Kashmir": "North", "Ladakh": "North",
            "Tamil Nadu": "South", "Karnataka": "South", "Kerala": "South",
            "Andhra Pradesh": "South", "Telangana": "South", "Puducherry": "South",
            "West Bengal": "East", "Bihar": "East", "Jharkhand": "East", "Odisha": "East",
            "Sikkim": "East", "Assam": "Northeast", "Meghalaya": "Northeast",
            "Manipur": "Northeast", "Mizoram": "Northeast", "Tripura": "Northeast",
            "Arunachal Pradesh": "Northeast", "Nagaland": "Northeast",
            "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
        }
        df["region"] = df["state_clean"].map(region_map).fillna("Other")

        # Date columns
        df["quarter_start_date"] = pd.to_datetime(
            df.apply(lambda r: f"{r['year']}-{(r['quarter']-1)*3 + 1:02d}-01", axis=1)
        )

        # Type enforcement
        df["transaction_count"] = df["transaction_count"].astype(np.int64)
        df["transaction_amount"] = df["transaction_amount"].astype(np.float64)

        # Derived metric
        df["avg_transaction_value"] = np.where(
            df["transaction_count"] > 0,
            df["transaction_amount"] / df["transaction_count"],
            0.0,
        )

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        # Validate
        DataValidator(df, "District Transactions").check_not_empty().check_no_nulls(
            ["year", "quarter", "state", "district", "transaction_count"]
        ).check_positive_values(
            ["transaction_count", "transaction_amount"]
        ).report(self.reports / "district_transactions.json")

        # Write district-level
        out = self.silver / "geographic" / "district_transactions.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)

        # Also write state-level aggregation
        state_agg = (
            df.groupby(["year", "quarter", "quarter_start_date", "state_clean", "region"])
            .agg(
                total_txn_count=("transaction_count", "sum"),
                total_txn_amount=("transaction_amount", "sum"),
                num_districts=("district_clean", "nunique"),
                avg_txn_value=("avg_transaction_value", "mean"),
            )
            .reset_index()
        )
        state_out = self.silver / "geographic" / "state_transactions.parquet"
        state_agg.to_parquet(state_out, index=False)

        logger.success(
            f"✅ {len(df)} district + {len(state_agg)} state records → {out.parent}"
        )
        return True

    # ── PhonePe Users ────────────────────────────────────────────────

    def _transform_phonepe_users(self) -> bool:
        """Clean PhonePe user registration and device data.

        Bronze has two record types mixed: aggregate (registered_users) and
        device-brand rows. We split into two Silver outputs.
        """
        src = self.bronze / "phonepe_pulse" / "agg_users_country.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)

        df["quarter_start_date"] = pd.to_datetime(
            df.apply(lambda r: f"{r['year']}-{(r['quarter']-1)*3 + 1:02d}-01", axis=1)
        )
        drop_cols = ["source", "ingested_at", "granularity", "region"]

        # --- Aggregate user registrations (28 rows: 1 per quarter) ---
        agg = df[df["registered_users"].notna()].copy()
        agg["registered_users"] = agg["registered_users"].astype(np.int64)
        agg["app_opens"] = agg["app_opens"].astype(np.int64)
        agg = agg.drop(columns=drop_cols + ["device_brand", "device_count", "device_percentage"], errors="ignore")

        DataValidator(agg, "PhonePe User Aggregates").check_not_empty().check_no_nulls(
            ["year", "quarter", "registered_users"]
        ).check_positive_values(["registered_users"]).report(
            self.reports / "phonepe_users_agg.json"
        )

        out_agg = self.silver / "users" / "phonepe_user_aggregates.parquet"
        out_agg.parent.mkdir(parents=True, exist_ok=True)
        agg.to_parquet(out_agg, index=False)

        # --- Device brand breakdown (187 rows) ---
        dev = df[df["device_brand"].notna()].copy()
        dev["device_brand_clean"] = dev["device_brand"].str.strip().str.title()
        dev["device_count"] = dev["device_count"].astype(np.int64)
        dev = dev.drop(columns=drop_cols + ["registered_users", "app_opens"], errors="ignore")

        DataValidator(dev, "PhonePe Device Brands").check_not_empty().check_no_nulls(
            ["year", "quarter", "device_brand", "device_count"]
        ).check_positive_values(["device_count"]).report(
            self.reports / "phonepe_users_devices.json"
        )

        out_dev = self.silver / "users" / "phonepe_device_brands.parquet"
        dev.to_parquet(out_dev, index=False)

        logger.success(f"✅ {len(agg)} user aggregate + {len(dev)} device records → {out_agg.parent}")
        return True

    # ── PhonePe Insurance ────────────────────────────────────────────

    def _transform_phonepe_insurance(self) -> bool:
        """Clean PhonePe insurance transaction data."""
        src = self.bronze / "phonepe_pulse" / "aggregated_insurance.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)

        df["quarter_start_date"] = pd.to_datetime(
            df.apply(lambda r: f"{r['year']}-{(r['quarter']-1)*3 + 1:02d}-01", axis=1)
        )
        df["count"] = df["count"].astype(np.int64)
        df["amount"] = df["amount"].astype(np.float64)

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        DataValidator(df, "PhonePe Insurance").check_not_empty().check_no_nulls(
            ["year", "quarter", "count", "amount"]
        ).check_positive_values(["count", "amount"]).report(
            self.reports / "phonepe_insurance.json"
        )

        out = self.silver / "transactions" / "phonepe_insurance.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} insurance records → {out}")
        return True

    # ── PhonePe Top Transactions ─────────────────────────────────────

    def _transform_phonepe_top(self) -> bool:
        """Clean PhonePe top transactions by state/district/pincode."""
        src = self.bronze / "phonepe_pulse" / "top_transactions.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)

        df["quarter_start_date"] = pd.to_datetime(
            df.apply(lambda r: f"{r['year']}-{(r['quarter']-1)*3 + 1:02d}-01", axis=1)
        )
        df["entity_name_clean"] = df["entity_name"].str.strip().str.title()
        df["count"] = df["count"].astype(np.int64)
        df["amount"] = df["amount"].astype(np.float64)

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        DataValidator(df, "PhonePe Top Transactions").check_not_empty().check_no_nulls(
            ["year", "quarter", "level", "entity_name", "count", "amount"]
        ).check_positive_values(["count", "amount"]).report(
            self.reports / "phonepe_top.json"
        )

        out = self.silver / "transactions" / "phonepe_top_transactions.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} top transaction records → {out}")
        return True

    # ── NPCI Monthly Volumes ─────────────────────────────────────────

    def _transform_npci_volumes(self) -> bool:
        """Clean NPCI monthly volume data — add fiscal year, validate growth."""
        src = self.bronze / "npci" / "monthly_upi_volumes.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)
        df["date"] = pd.to_datetime(df["date"])

        # Indian fiscal year (April–March)
        df["fiscal_year"] = df["date"].apply(
            lambda d: f"FY{d.year}-{str(d.year+1)[-2:]}" if d.month >= 4
            else f"FY{d.year-1}-{str(d.year)[-2:]}"
        )

        # Fiscal quarter
        df["fiscal_quarter"] = df["date"].dt.month.apply(
            lambda m: f"Q{((m - 4) % 12) // 3 + 1}"
        )

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        DataValidator(df, "NPCI Monthly Volumes").check_not_empty().check_no_nulls(
            ["year", "month", "date", "transaction_volume_billions"]
        ).check_positive_values(
            ["transaction_volume_billions", "transaction_value_lakh_crores"]
        ).check_date_range("date", min_year=2022).report(
            self.reports / "npci_volumes.json"
        )

        out = self.silver / "transactions" / "npci_monthly_volumes.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} NPCI monthly records → {out}")
        return True

    # ── NPCI Market Share ────────────────────────────────────────────

    def _transform_npci_market_share(self) -> bool:
        """Clean NPCI app market share data."""
        src = self.bronze / "npci" / "app_market_share.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)
        df["date"] = pd.to_datetime(df["date"])

        # Standardize app names
        df["app_name_clean"] = df["app_name"].str.strip()

        # Flag top-2 duopoly players
        df["is_top2"] = df["app_name_clean"].isin(["PhonePe", "Google Pay"])

        # Parent company mapping
        parent_map = {
            "PhonePe": "Walmart/PhonePe",
            "Google Pay": "Alphabet/Google",
            "Paytm": "One97 Communications",
            "CRED": "CRED (Kunal Shah)",
            "Amazon Pay": "Amazon",
            "WhatsApp Pay": "Meta",
            "Others": "Various",
        }
        df["parent_company"] = df["app_name_clean"].map(parent_map).fillna("Other")

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        DataValidator(df, "NPCI Market Share").check_not_empty().check_no_nulls(
            ["date", "app_name", "market_share_pct"]
        ).check_no_duplicates(
            ["date", "app_name"]
        ).report(self.reports / "npci_market_share.json")

        out = self.silver / "market_share" / "app_market_share.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} market share records → {out}")
        return True

    # ── RBI Currency in Circulation ──────────────────────────────────

    def _transform_rbi_currency(self) -> bool:
        """Clean RBI currency-in-circulation data."""
        src = self.bronze / "rbi" / "currency_in_circulation.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)
        df["date"] = pd.to_datetime(df["date"])

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        DataValidator(df, "RBI Currency in Circulation").check_not_empty().check_no_nulls(
            ["date", "currency_in_circulation_lakh_cr"]
        ).check_positive_values(
            ["currency_in_circulation_lakh_cr"]
        ).check_date_range("date", min_year=2019).report(
            self.reports / "rbi_currency.json"
        )

        out = self.silver / "transactions" / "rbi_currency_circulation.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} RBI currency records → {out}")
        return True

    # ── RBI ATM Transactions ─────────────────────────────────────────

    def _transform_rbi_atm(self) -> bool:
        """Clean RBI ATM transaction data."""
        src = self.bronze / "rbi" / "atm_transactions.parquet"
        if not src.exists():
            logger.warning(f"Missing: {src}")
            return False

        df = pd.read_parquet(src)

        # Create date from year + quarter
        df["quarter_start_date"] = pd.to_datetime(
            df.apply(lambda r: f"{r['year']}-{(r['quarter']-1)*3 + 1:02d}-01", axis=1)
        )

        df = df.drop(columns=["source", "ingested_at"], errors="ignore")

        DataValidator(df, "RBI ATM Transactions").check_not_empty().check_no_nulls(
            ["year", "quarter", "atm_transactions_millions"]
        ).check_positive_values(
            ["atm_transactions_millions"]
        ).report(self.reports / "rbi_atm.json")

        out = self.silver / "transactions" / "rbi_atm_transactions.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        logger.success(f"✅ {len(df)} ATM transaction records → {out}")
        return True
