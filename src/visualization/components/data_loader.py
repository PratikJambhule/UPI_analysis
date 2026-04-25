"""Centralized data loading for the Streamlit dashboard."""

import pandas as pd
import streamlit as st
from pathlib import Path

GOLD_EXPORTS = Path("data/gold/exports")
SILVER_DIR = Path("data/silver")

# Silver files that supplement the Gold layer.
# On Streamlit Cloud, these are pre-copied into gold/exports.
# Locally, they fall back to the silver directory.
_SILVER_FALLBACKS = {
    "app_market_share": "market_share/app_market_share.parquet",
    "phonepe_user_aggregates": "users/phonepe_user_aggregates.parquet",
    "phonepe_device_brands": "users/phonepe_device_brands.parquet",
    "phonepe_insurance": "transactions/phonepe_insurance.parquet",
    "rbi_atm_transactions": "transactions/rbi_atm_transactions.parquet",
    "npci_monthly_volumes": "transactions/npci_monthly_volumes.parquet",
    "rbi_currency_circulation": "transactions/rbi_currency_circulation.parquet",
    "phonepe_top_transactions": "transactions/phonepe_top_transactions.parquet",
    "district_transactions": "geographic/district_transactions.parquet",
    "state_transactions": "geographic/state_transactions.parquet",
}


@st.cache_data(ttl=3600)
def load_all_data() -> dict[str, pd.DataFrame]:
    """Load all Gold layer exports + supplementary Silver data."""
    if not GOLD_EXPORTS.exists():
        return {}

    data: dict[str, pd.DataFrame] = {}

    # 1. Load everything from gold/exports (includes copied silver files on Cloud)
    for pf in GOLD_EXPORTS.glob("*.parquet"):
        try:
            data[pf.stem] = pd.read_parquet(pf)
        except Exception:
            continue

    # 2. Fallback: load from silver if not already loaded from gold
    for key, rel_path in _SILVER_FALLBACKS.items():
        if key not in data:
            path = SILVER_DIR / rel_path
            if path.exists():
                try:
                    data[key] = pd.read_parquet(path)
                except Exception:
                    continue

    return data


@st.cache_data(ttl=86400)
def load_india_geojson() -> dict | None:
    """Load India states GeoJSON — local file or public URL fallback."""
    import json

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


def get_available_years(data: dict[str, pd.DataFrame]) -> list[int]:
    """Extract available years from fact_upi_transactions."""
    if "fact_upi_transactions" in data and not data["fact_upi_transactions"].empty:
        return sorted(data["fact_upi_transactions"]["year"].unique())
    return list(range(2018, 2026))
