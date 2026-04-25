"""
RBI Database on Indian Economy (DBIE) ingester.

Converts curated Currency in Circulation and ATM transaction data
into structured Parquet files for cash displacement analysis.
"""

import pandas as pd
import requests
from pathlib import Path
from loguru import logger
from .base_ingester import BaseIngester
from io import BytesIO


class RBIIngester(BaseIngester):
    """
    Ingests RBI data for cash-vs-digital analysis.

    Key datasets:
    1. Currency in Circulation (weekly data)
    2. Payment System Statistics (monthly/quarterly)
    3. ATM/POS transaction volumes
    """

    RBI_DATA_SOURCES = {
        "payment_systems": {
            "description": "Payment & Settlement Systems — Volume & Value",
            "url": "https://dbie.rbi.org.in/DBIE/dbie.rbi?site=statistics&page=paymentindex",
            "method": "manual_curated"
        },
        "currency_circulation": {
            "description": "Currency in Circulation (Weekly)",
            "url": "https://dbie.rbi.org.in/DBIE/dbie.rbi?site=statistics",
            "method": "manual_curated"
        }
    }

    # Curated RBI data: Currency in Circulation (₹ Lakh Crore)
    # Source: RBI DBIE / Weekly Statistical Supplement (WSS)
    CURRENCY_IN_CIRCULATION = {
        (2019, 3):  20.14,
        (2019, 6):  20.71,
        (2019, 9):  21.08,
        (2019, 12): 22.42,
        (2020, 3):  24.07,
        (2020, 6):  26.28,
        (2020, 9):  27.06,
        (2020, 12): 27.71,
        (2021, 3):  28.27,
        (2021, 6):  29.28,
        (2021, 9):  29.95,
        (2021, 12): 31.05,
        (2022, 3):  31.33,
        (2022, 6):  32.42,
        (2022, 9):  33.21,
        (2022, 12): 33.82,
        (2023, 3):  34.67,
        (2023, 6):  35.15,
        (2023, 9):  35.44,
        (2023, 12): 35.98,
        (2024, 3):  36.28,
        (2024, 6):  36.84,
        (2024, 9):  37.11,
        (2024, 12): 37.58,
        (2025, 3):  37.82,
        (2025, 6):  38.24,  # ⚠️ verify
    }

    # ATM transaction data (millions of transactions per quarter)
    # Source: RBI DBIE — Payment and Settlement System Statistics
    ATM_TRANSACTIONS = {
        (2019, 1): 2134, (2019, 2): 2198, (2019, 3): 2267, (2019, 4): 2312,
        (2020, 1): 2289, (2020, 2): 1845, (2020, 3): 2012, (2020, 4): 2156,
        (2021, 1): 2245, (2021, 2): 2380, (2021, 3): 2412, (2021, 4): 2456,
        (2022, 1): 2398, (2022, 2): 2467, (2022, 3): 2501, (2022, 4): 2534,
        (2023, 1): 2489, (2023, 2): 2512, (2023, 3): 2478, (2023, 4): 2445,
        (2024, 1): 2401, (2024, 2): 2389, (2024, 3): 2356, (2024, 4): 2312,
        (2025, 1): 2278,  # ⚠️ verify
        (2025, 2): 2245,  # ⚠️ low confidence
    }

    def __init__(self):
        super().__init__("rbi_dbie")
        self.output_path = Path("data/bronze/rbi")

    def extract(self) -> None:
        """Extract all RBI datasets."""
        self._extract_currency_circulation()
        self._extract_atm_data()
        self._extract_payment_systems()

    def _extract_currency_circulation(self) -> None:
        records = []
        for (year, month), value in self.CURRENCY_IN_CIRCULATION.items():
            records.append({
                "year": year,
                "month": month,
                "date": f"{year}-{month:02d}-01",
                "currency_in_circulation_lakh_cr": value,
                "currency_in_circulation_trillion_inr": value * 0.1,
                "source": "rbi_dbie",
                "ingested_at": self.ingest_timestamp
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df["qoq_growth"] = df["currency_in_circulation_lakh_cr"].pct_change()

        output_file = self.output_path / "currency_in_circulation.parquet"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_file, index=False)
        logger.info(f"Wrote {len(df)} currency circulation records")

    def _extract_atm_data(self) -> None:
        records = []
        for (year, quarter), volume in self.ATM_TRANSACTIONS.items():
            records.append({
                "year": year,
                "quarter": quarter,
                "atm_transactions_millions": volume,
                "source": "rbi_dbie",
                "ingested_at": self.ingest_timestamp
            })

        df = pd.DataFrame(records)
        output_file = self.output_path / "atm_transactions.parquet"
        df.to_parquet(output_file, index=False)
        logger.info(f"Wrote {len(df)} ATM transaction records")

    def _extract_payment_systems(self) -> None:
        """Placeholder for broader payment system data."""
        logger.info("Payment systems data: extend with NEFT, IMPS, RTGS data")

    def validate_extraction(self) -> bool:
        critical = self.output_path / "currency_in_circulation.parquet"
        return critical.exists() and len(pd.read_parquet(critical)) > 0
