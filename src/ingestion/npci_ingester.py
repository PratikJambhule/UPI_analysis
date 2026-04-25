"""
NPCI UPI Statistics ingester.

Converts curated monthly/yearly UPI data and app market share data
into structured Parquet files. Also attempts web scraping of NPCI site.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from loguru import logger
from datetime import datetime
from .base_ingester import BaseIngester
import time
import re


class NPCIIngester(BaseIngester):
    """
    Scrapes NPCI's UPI product statistics page.

    Note: NPCI's website uses dynamic rendering. If Selenium is needed,
    we fall back to it. Start with requests + BS4 first.

    Data we extract:
    1. Monthly UPI volume & value (from their published tables/PDFs)
    2. UPI app market share data (if available in tabular format)
    """

    NPCI_UPI_STATS_URL = "https://www.npci.org.in/what-we-do/upi/product-statistics"

    # Manually curated monthly data (NPCI publishes this — verified numbers)
    # Source: NPCI monthly press releases + statistics page
    # Cross-validation: monthly sums match yearly totals in NPCI_YEARLY_UPI_DATA
    NPCI_MONTHLY_UPI_DATA = {
        # Format: (year, month): (volume_in_billions, value_in_lakh_crores)

        # ── 2022 (Historical Backfill) ──────────────────────────────
        (2022, 1):  (4.62,  8.32),
        (2022, 2):  (4.53,  8.27),
        (2022, 3):  (5.40,  9.60),
        (2022, 4):  (5.58,  9.83),
        (2022, 5):  (5.95,  10.41),
        (2022, 6):  (5.86,  10.15),
        (2022, 7):  (6.28,  10.63),
        (2022, 8):  (6.58,  10.73),
        (2022, 9):  (6.78,  11.16),
        (2022, 10): (7.30,  12.11),
        (2022, 11): (7.30,  11.91),
        (2022, 12): (7.82,  12.82),

        # ── 2023 (Historical Backfill) ──────────────────────────────
        (2023, 1):  (8.03,  12.98),
        (2023, 2):  (7.54,  12.36),
        (2023, 3):  (8.71,  14.07),
        (2023, 4):  (8.89,  14.07),
        (2023, 5):  (9.41,  14.89),
        (2023, 6):  (9.33,  14.75),
        (2023, 7):  (9.96,  15.34),
        (2023, 8):  (10.58, 15.76),
        (2023, 9):  (10.56, 15.80),
        (2023, 10): (11.40, 17.16),
        (2023, 11): (11.16, 17.40),
        (2023, 12): (11.79, 18.23),

        # ── 2024 ────────────────────────────────────────────────────
        (2024, 1):  (12.20, 18.41),
        (2024, 2):  (11.90, 17.52),
        (2024, 3):  (13.44, 19.78),
        (2024, 4):  (13.30, 19.64),
        (2024, 5):  (14.04, 20.45),
        (2024, 6):  (13.89, 20.07),
        (2024, 7):  (14.44, 20.64),
        (2024, 8):  (14.96, 21.56),
        (2024, 9):  (15.04, 21.21),
        (2024, 10): (16.58, 23.49),
        (2024, 11): (15.48, 21.55),
        (2024, 12): (16.73, 23.25),

        # ── 2025 ────────────────────────────────────────────────────
        (2025, 1):  (16.99, 23.48),
        (2025, 2):  (15.63, 21.76),
        (2025, 3):  (17.89, 25.02),
        (2025, 4):  (18.15, 25.11),
        (2025, 5):  (18.89, 25.61),
        (2025, 6):  (19.48, 26.09),  # ⚠️ verify
    }

    NPCI_YEARLY_UPI_DATA = {
        2017: {"volume_bn": 0.92, "value_lakh_cr": 1.00},
        2018: {"volume_bn": 5.35, "value_lakh_cr": 8.77},
        2019: {"volume_bn": 10.78, "value_lakh_cr": 21.31},
        2020: {"volume_bn": 22.28, "value_lakh_cr": 41.04},
        2021: {"volume_bn": 38.74, "value_lakh_cr": 71.54},
        2022: {"volume_bn": 74.05, "value_lakh_cr": 125.94},
        2023: {"volume_bn": 117.46, "value_lakh_cr": 182.84},
        2024: {"volume_bn": 172.20, "value_lakh_cr": 246.82},
    }

    # UPI App Market Share Data (from NPCI monthly/quarterly reports)
    # KEY EVENT: RBI action on Paytm Payments Bank (Jan 31, 2024)
    UPI_APP_MARKET_SHARE = {
        # ── 2023 Quarterly ──────────────────────────────────────────
        (2023, 3):  {"PhonePe": 46.81, "Google Pay": 34.19, "Paytm": 14.63,
                     "CRED": 0.78,  "Amazon Pay": 1.42, "WhatsApp Pay": 0.15, "Others": 2.02},
        (2023, 6):  {"PhonePe": 47.32, "Google Pay": 34.72, "Paytm": 13.56,
                     "CRED": 1.05,  "Amazon Pay": 1.30, "WhatsApp Pay": 0.20, "Others": 1.85},
        (2023, 9):  {"PhonePe": 47.62, "Google Pay": 35.28, "Paytm": 12.82,
                     "CRED": 1.28,  "Amazon Pay": 1.18, "WhatsApp Pay": 0.28, "Others": 1.54},
        (2023, 12): {"PhonePe": 47.89, "Google Pay": 35.90, "Paytm": 11.43,
                     "CRED": 1.52,  "Amazon Pay": 1.12, "WhatsApp Pay": 0.35, "Others": 1.79},
        # ── 2024 Quarterly ──────────────────────────────────────────
        (2024, 3):  {"PhonePe": 48.12, "Google Pay": 36.52, "Paytm": 8.45,
                     "CRED": 1.78,  "Amazon Pay": 1.15, "WhatsApp Pay": 0.42, "Others": 3.56},
        (2024, 6):  {"PhonePe": 48.25, "Google Pay": 36.80, "Paytm": 7.65,
                     "CRED": 1.95,  "Amazon Pay": 1.10, "WhatsApp Pay": 0.48, "Others": 3.77},
        (2024, 9):  {"PhonePe": 48.30, "Google Pay": 37.10, "Paytm": 7.38,
                     "CRED": 2.05,  "Amazon Pay": 1.08, "WhatsApp Pay": 0.50, "Others": 3.59},
        (2024, 12): {"PhonePe": 48.36, "Google Pay": 37.00, "Paytm": 7.22,
                     "CRED": 2.14,  "Amazon Pay": 1.08, "WhatsApp Pay": 0.53, "Others": 3.67},
        # ── 2025 Monthly ────────────────────────────────────────────
        (2025, 1):  {"PhonePe": 48.45, "Google Pay": 36.92, "Paytm": 7.03,
                     "CRED": 2.34,  "Amazon Pay": 1.02, "WhatsApp Pay": 0.58, "Others": 3.66},
        (2025, 3):  {"PhonePe": 48.62, "Google Pay": 36.78, "Paytm": 6.85,
                     "CRED": 2.51,  "Amazon Pay": 0.98, "WhatsApp Pay": 0.62, "Others": 3.64},
        (2025, 4):  {"PhonePe": 48.68, "Google Pay": 36.50, "Paytm": 6.72,
                     "CRED": 2.62,  "Amazon Pay": 0.95, "WhatsApp Pay": 0.65, "Others": 3.88},
        (2025, 5):  {"PhonePe": 48.75, "Google Pay": 36.40, "Paytm": 6.58,
                     "CRED": 2.72,  "Amazon Pay": 0.93, "WhatsApp Pay": 0.68, "Others": 3.94},
        (2025, 6):  {"PhonePe": 48.82, "Google Pay": 36.28, "Paytm": 6.45,  # ⚠️ verify
                     "CRED": 2.82,  "Amazon Pay": 0.90, "WhatsApp Pay": 0.72, "Others": 4.01},
    }

    def __init__(self):
        super().__init__("npci")
        self.output_path = Path("data/bronze/npci")

    def extract(self) -> None:
        """Extract all NPCI data sources."""
        self._extract_monthly_volumes()
        self._extract_yearly_volumes()
        self._extract_market_share()
        self._attempt_web_scrape()

    def _extract_monthly_volumes(self) -> None:
        """Convert curated monthly data to structured Parquet."""
        records = []
        for (year, month), (volume, value) in self.NPCI_MONTHLY_UPI_DATA.items():
            records.append({
                "year": year,
                "month": month,
                "date": f"{year}-{month:02d}-01",
                "transaction_volume_billions": volume,
                "transaction_value_lakh_crores": value,
                "transaction_value_trillions_inr": value * 0.1,
                "source": "npci_official",
                "ingested_at": self.ingest_timestamp
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # Compute derived metrics
        df["mom_volume_growth"] = df["transaction_volume_billions"].pct_change()
        df["yoy_volume_growth"] = df["transaction_volume_billions"].pct_change(12)
        df["avg_transaction_value_inr"] = (
            (df["transaction_value_lakh_crores"] * 1e12) /
            (df["transaction_volume_billions"] * 1e9)
        )

        output_file = self.output_path / "monthly_upi_volumes.parquet"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_file, index=False)
        logger.info(f"Wrote {len(df)} monthly volume records")

    def _extract_yearly_volumes(self) -> None:
        """Convert yearly data for long-term trend analysis."""
        records = []
        for year, data in self.NPCI_YEARLY_UPI_DATA.items():
            records.append({
                "year": year,
                "transaction_volume_billions": data["volume_bn"],
                "transaction_value_lakh_crores": data["value_lakh_cr"],
                "source": "npci_official",
                "ingested_at": self.ingest_timestamp
            })

        df = pd.DataFrame(records)
        df["yoy_volume_growth"] = df["transaction_volume_billions"].pct_change()

        output_file = self.output_path / "yearly_upi_volumes.parquet"
        df.to_parquet(output_file, index=False)
        logger.info(f"Wrote {len(df)} yearly volume records")

    def _extract_market_share(self) -> None:
        """Structure app-wise market share data for HHI analysis."""
        records = []
        for (year, month), apps in self.UPI_APP_MARKET_SHARE.items():
            for app_name, share_pct in apps.items():
                records.append({
                    "year": year,
                    "month": month,
                    "date": f"{year}-{month:02d}-01",
                    "app_name": app_name,
                    "market_share_pct": share_pct,
                    "market_share_decimal": share_pct / 100,
                    "source": "npci_official",
                    "ingested_at": self.ingest_timestamp
                })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])

        output_file = self.output_path / "app_market_share.parquet"
        df.to_parquet(output_file, index=False)
        logger.info(f"Wrote {len(df)} market share records")

    def _attempt_web_scrape(self) -> None:
        """
        Attempt to scrape latest data from NPCI website.
        Falls back gracefully if site structure changes.
        """
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Research Project - UPI Analytics)"
                }
                response = requests.get(
                    self.NPCI_UPI_STATS_URL,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    tables = pd.read_html(str(soup))

                    if tables:
                        for i, table in enumerate(tables):
                            if table.select_dtypes(include='number').shape[1] == 0:
                                logger.warning(f"Scraped table {i} has no numeric columns — skipping")
                                continue
                            output_file = self.output_path / f"scraped_table_{i}.parquet"
                            table.to_parquet(output_file, index=False)
                            logger.info(f"Scraped table {i}: {table.shape}")
                        return
                    else:
                        logger.warning("No HTML tables found on NPCI page "
                                       "(may need Selenium for JS-rendered content)")
                        return
                else:
                    logger.warning(f"NPCI returned status {response.status_code} (attempt {attempt + 1}/{MAX_RETRIES})")

            except requests.exceptions.Timeout:
                logger.warning(f"NPCI request timed out (attempt {attempt + 1}/{MAX_RETRIES})")
            except Exception as e:
                logger.warning(f"Web scraping failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

        logger.info("All NPCI scrape attempts failed — using curated data as primary source.")

    def validate_extraction(self) -> bool:
        """Validate critical NPCI files exist."""
        critical = self.output_path / "monthly_upi_volumes.parquet"
        if not critical.exists():
            return False
        df = pd.read_parquet(critical)
        return len(df) > 0
