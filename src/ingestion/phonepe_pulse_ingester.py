"""
PhonePe Pulse GitHub repository ingester.

Parses the 9,026+ JSON files from the PhonePe Pulse open dataset
into structured Parquet files in data/bronze/phonepe_pulse/.
"""

import json
import subprocess
import pandas as pd
from pathlib import Path
from loguru import logger
from .base_ingester import BaseIngester


class PhonePePulseIngester(BaseIngester):
    """Ingests data from PhonePe Pulse GitHub repository."""

    REPO_URL = "https://github.com/PhonePe/pulse.git"

    def __init__(self):
        super().__init__("phonepe_pulse")
        self.repo_path = Path(self.config.get("local_path", "data/bronze/phonepe_pulse/repo"))
        self.output_path = Path("data/bronze/phonepe_pulse")

    def extract(self) -> None:
        self._sync_repo()
        self._parse_aggregated_transactions()
        self._parse_aggregated_users()
        self._parse_map_transactions()
        self._parse_aggregated_insurance()
        self._parse_top_transactions()

    def _sync_repo(self) -> None:
        """Git clone if first time, git pull if repo exists."""
        if (self.repo_path / ".git").exists():
            logger.info("PhonePe Pulse repo exists. Pulling latest...")
            subprocess.run(
                ["git", "-C", str(self.repo_path), "pull", "origin", "master"],
                check=True, capture_output=True
            )
        else:
            logger.info("Cloning PhonePe Pulse repo (first time)...")
            self.repo_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--depth", "1", self.REPO_URL, str(self.repo_path)],
                check=True, capture_output=True
            )
        logger.success("Repo sync complete.")

    def _iter_year_quarter(self, base: Path):
        """Yield (year, quarter, data) for each JSON under base/{year}/{quarter}.json."""
        if not base.exists():
            logger.warning(f"Path does not exist: {base}")
            return

        for year_dir in sorted(base.iterdir()):
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue
            year = int(year_dir.name)

            for quarter_file in sorted(year_dir.glob("*.json")):
                quarter = int(quarter_file.stem)
                try:
                    data = json.loads(quarter_file.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.warning(f"Failed to parse {quarter_file}: {e}")
                    continue

                if not data.get("success"):
                    continue

                yield year, quarter, data

    def _parse_aggregated_transactions(self) -> None:
        """Parse country-level aggregated transaction data."""
        records = []
        base = self.repo_path / "data" / "aggregated" / "transaction" / "country" / "india"

        for year, quarter, data in self._iter_year_quarter(base):
            for txn_category in data["data"]["transactionData"]:
                category_name = txn_category["name"]
                for instrument in txn_category["paymentInstruments"]:
                    records.append({
                        "year": year,
                        "quarter": quarter,
                        "category": category_name,
                        "instrument_type": instrument["type"],
                        "transaction_count": instrument["count"],
                        "transaction_amount": instrument["amount"],
                        "granularity": "country",
                        "region": "india",
                        "source": "phonepe_pulse",
                        "ingested_at": self.ingest_timestamp
                    })

        df = pd.DataFrame(records)
        output_file = self.output_path / "agg_transactions_country.parquet"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_file, index=False, engine="pyarrow")
        logger.info(f"Wrote {len(df)} records to {output_file}")

    def _parse_map_transactions(self) -> None:
        """Parse district-level (map) transaction data — the most valuable dataset."""
        records = []
        base = self.repo_path / "data" / "map" / "transaction" / "hover" / "country" / "india" / "state"

        if not base.exists():
            logger.warning(f"Map data path does not exist: {base}")
            return

        for state_dir in sorted(base.iterdir()):
            if not state_dir.is_dir():
                continue
            state_name = state_dir.name

            for year, quarter, data in self._iter_year_quarter(state_dir):
                for district_data in data["data"].get("hoverDataList", []):
                    district_name = district_data["name"]
                    for metric in district_data["metric"]:
                        records.append({
                            "year": year,
                            "quarter": quarter,
                            "state": state_name,
                            "district": district_name,
                            "metric_type": metric["type"],
                            "transaction_count": metric["count"],
                            "transaction_amount": metric["amount"],
                            "source": "phonepe_pulse",
                            "ingested_at": self.ingest_timestamp
                        })

        df = pd.DataFrame(records)
        output_file = self.output_path / "map_transactions_district.parquet"
        df.to_parquet(output_file, index=False, engine="pyarrow")
        logger.info(f"Wrote {len(df)} district-level records to {output_file}")

    def _parse_aggregated_users(self) -> None:
        """Parse user registration data (country level)."""
        records = []
        base = self.repo_path / "data" / "aggregated" / "user" / "country" / "india"

        for year, quarter, data in self._iter_year_quarter(base):
            user_data = data["data"]["aggregated"]
            registered_users = user_data.get("registeredUsers", 0)
            app_opens = user_data.get("appOpens", 0)

            records.append({
                "year": year,
                "quarter": quarter,
                "registered_users": registered_users,
                "app_opens": app_opens,
                "granularity": "country",
                "region": "india",
                "source": "phonepe_pulse",
                "ingested_at": self.ingest_timestamp
            })

            for brand_data in data["data"].get("usersByDevice") or []:
                records.append({
                    "year": year,
                    "quarter": quarter,
                    "device_brand": brand_data.get("brand", "Unknown"),
                    "device_count": brand_data.get("count", 0),
                    "device_percentage": brand_data.get("percentage", 0),
                    "granularity": "country",
                    "region": "india",
                    "source": "phonepe_pulse",
                    "ingested_at": self.ingest_timestamp
                })

        df = pd.DataFrame(records)
        output_file = self.output_path / "agg_users_country.parquet"
        df.to_parquet(output_file, index=False, engine="pyarrow")
        logger.info(f"Wrote {len(df)} user records to {output_file}")

    def _parse_aggregated_insurance(self) -> None:
        """Parse insurance transaction data."""
        records = []
        base = self.repo_path / "data" / "aggregated" / "insurance" / "country" / "india"

        for year, quarter, data in self._iter_year_quarter(base):
            for item in data["data"].get("transactionData", []):
                category = item.get("name", "Unknown")
                for pi in item.get("paymentInstruments", []):
                    records.append({
                        "year": year,
                        "quarter": quarter,
                        "category": category,
                        "type": pi.get("type", ""),
                        "count": pi.get("count", 0),
                        "amount": pi.get("amount", 0.0),
                        "source": "phonepe_pulse",
                        "data_type": "aggregated_insurance",
                        "ingested_at": self.ingest_timestamp,
                    })

        if records:
            df = pd.DataFrame(records)
            output_file = self.output_path / "aggregated_insurance.parquet"
            df.to_parquet(output_file, index=False, engine="pyarrow")
            logger.info(f"Wrote {len(df)} insurance records to {output_file}")
        else:
            logger.warning("No insurance records parsed")

    def _parse_top_transactions(self) -> None:
        """Parse top states/districts/pincodes by transaction volume."""
        records = []
        base = self.repo_path / "data" / "top" / "transaction" / "country" / "india"

        for year, quarter, data in self._iter_year_quarter(base):
            for level in ["states", "districts", "pincodes"]:
                for item in data["data"].get(level, []):
                    entity = item.get("entityName", "Unknown")
                    metric = item.get("metric", {})
                    records.append({
                        "year": year,
                        "quarter": quarter,
                        "level": level,
                        "entity_name": entity,
                        "count": metric.get("count", 0),
                        "amount": metric.get("amount", 0.0),
                        "source": "phonepe_pulse",
                        "data_type": "top_transaction",
                        "ingested_at": self.ingest_timestamp,
                    })

        if records:
            df = pd.DataFrame(records)
            output_file = self.output_path / "top_transactions.parquet"
            df.to_parquet(output_file, index=False, engine="pyarrow")
            logger.info(f"Wrote {len(df)} top transaction records to {output_file}")

    def validate_extraction(self) -> bool:
        """Validate that critical Parquet files were created and non-empty."""
        critical_files = [
            self.output_path / "agg_transactions_country.parquet",
            self.output_path / "map_transactions_district.parquet",
        ]

        for f in critical_files:
            if not f.exists():
                logger.error(f"Missing critical file: {f}")
                return False

            df = pd.read_parquet(f)
            if len(df) == 0:
                logger.error(f"Empty file: {f}")
                return False

            logger.info(f"✓ {f.name}: {len(df)} records, "
                       f"years {df['year'].min()}-{df['year'].max()}")

        return True
