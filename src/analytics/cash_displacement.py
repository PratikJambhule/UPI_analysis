"""
Cash Displacement Analysis.

Core Question: Is India actually going cashless, or is UPI adding new
transaction volume without replacing cash?

Metrics:
1. Digital-to-Cash Ratio: UPI value / Currency in Circulation
2. Displacement Velocity: Rate of change of the ratio (MoM)
3. Cash Growth vs UPI Growth: Comparative YoY growth rates
4. Cashless Threshold Analysis: When (if ever) will UPI value exceed CIC?
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Dict


class CashDisplacementAnalyzer:
    """Analyzes whether UPI is displacing cash or adding new transaction volume."""

    def __init__(self):
        self.gold_path = Path("data/gold/exports")
        self.output_path = Path("data/gold/exports")

    def run(self) -> bool:
        try:
            df = self._load_data()
            if df is None or len(df) < 3:
                logger.warning("Insufficient cash displacement data")
                return True

            analysis = self._compute_displacement_metrics(df)
            insights = self._generate_insights(analysis)
            self._save_results(analysis, insights)
            return True
        except Exception as e:
            logger.exception(f"Cash displacement analysis failed: {e}")
            return False

    def _load_data(self) -> pd.DataFrame:
        """Load pre-computed displacement data from Gold layer."""
        fact_file = self.gold_path / "fact_cash_displacement.parquet"
        if not fact_file.exists():
            logger.warning("fact_cash_displacement.parquet not found")
            return None

        df = pd.read_parquet(fact_file)
        # Convert date_key (YYYYMMDD int) to datetime
        df["date"] = pd.to_datetime(df["date_key"].astype(str), format="%Y%m%d")
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def _compute_displacement_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich with velocity, growth rates, and trend indicators."""
        # Displacement velocity (MoM change of ratio)
        df["displacement_velocity"] = df["digital_to_cash_ratio"].diff()
        df["velocity_pct"] = df["digital_to_cash_ratio"].pct_change() * 100

        # UPI growth rate (MoM)
        df["upi_volume_growth_pct"] = df["upi_volume_bn"].pct_change() * 100
        df["upi_value_growth_pct"] = df["upi_value_lakh_cr"].pct_change() * 100

        # CIC growth rate (QoQ, forward-filled so MoM captures when it changes)
        df["cic_growth_pct"] = df["cic_lakh_cr"].pct_change() * 100

        # Rolling averages (3-month) for smoother trends
        df["ratio_3m_avg"] = df["digital_to_cash_ratio"].rolling(3, min_periods=1).mean()
        df["velocity_3m_avg"] = df["displacement_velocity"].rolling(3, min_periods=1).mean()

        # YoY comparison (12-month lag)
        if len(df) >= 13:
            df["ratio_yoy_change"] = df["digital_to_cash_ratio"] - df["digital_to_cash_ratio"].shift(12)
            df["upi_volume_yoy_growth"] = (
                (df["upi_volume_bn"] / df["upi_volume_bn"].shift(12) - 1) * 100
            )

        # Trend classification
        df["trend"] = np.where(
            df["displacement_velocity"] > 0.01, "Accelerating",
            np.where(df["displacement_velocity"] < -0.01, "Decelerating", "Stable")
        )

        logger.info(f"Displacement metrics computed: {len(df)} months")
        return df

    def _generate_insights(self, df: pd.DataFrame) -> Dict:
        """Generate key insights about cash displacement."""
        first = df.iloc[0]
        latest = df.iloc[-1]

        ratio_start = first["digital_to_cash_ratio"]
        ratio_end = latest["digital_to_cash_ratio"]
        ratio_change = ratio_end - ratio_start
        months_span = len(df)

        # CIC trend: did cash actually decrease?
        cic_start = first["cic_lakh_cr"]
        cic_end = latest["cic_lakh_cr"]
        cic_grew = cic_end > cic_start

        # Average monthly velocity
        avg_velocity = df["displacement_velocity"].mean()

        # Months of accelerating vs decelerating
        accel_months = (df["trend"] == "Accelerating").sum()
        decel_months = (df["trend"] == "Decelerating").sum()

        insights = {
            "period": f"{first['date'].strftime('%b %Y')} to {latest['date'].strftime('%b %Y')}",
            "ratio_start": round(ratio_start, 4),
            "ratio_end": round(ratio_end, 4),
            "ratio_change": round(ratio_change, 4),
            "avg_monthly_velocity": round(avg_velocity, 4),
            "accelerating_months": int(accel_months),
            "decelerating_months": int(decel_months),
            "cic_grew": bool(cic_grew),
            "cic_start_lakh_cr": round(cic_start, 2),
            "cic_end_lakh_cr": round(cic_end, 2),

            "key_findings": [
                f"Digital-to-cash ratio grew from {ratio_start:.4f} to {ratio_end:.4f} "
                f"over {months_span} months — a {ratio_change / ratio_start * 100:.1f}% increase.",

                f"Despite UPI's explosive growth, currency in circulation {'increased' if cic_grew else 'decreased'} "
                f"from ₹{cic_start:.2f}L Cr to ₹{cic_end:.2f}L Cr.",

                "India is becoming 'less cash-dependent' rather than 'cashless' — "
                "UPI is creating additional digital transaction volume, especially in "
                "small-value payments (chai shops, auto-rickshaws, street vendors).",

                f"Displacement velocity: {accel_months} accelerating months vs "
                f"{decel_months} decelerating months.",

                f"At current velocity ({avg_velocity:.4f}/month), the ratio would reach "
                f"1.0 (parity) in ~{max(0, (1.0 - ratio_end) / avg_velocity):.0f} months "
                f"— but this is an extrapolation, not a prediction."
                if avg_velocity > 0 else
                "Displacement velocity is stagnant or negative — parity not on horizon.",
            ],
        }

        for finding in insights["key_findings"]:
            logger.info(f"💰 {finding}")

        return insights

    def _save_results(self, df: pd.DataFrame, insights: Dict) -> None:
        """Save enriched analysis."""
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Save enriched time series
        export_cols = [
            "date_key", "date", "upi_volume_bn", "upi_value_lakh_cr",
            "cic_lakh_cr", "digital_to_cash_ratio", "displacement_velocity",
            "velocity_pct", "upi_volume_growth_pct", "ratio_3m_avg",
            "velocity_3m_avg", "trend",
        ]
        # Only include columns that exist
        export_cols = [c for c in export_cols if c in df.columns]

        df[export_cols].to_parquet(
            self.output_path / "cash_displacement_analysis.parquet", index=False
        )
        logger.success(f"Cash displacement analysis saved: {len(df)} periods")
