"""
Herfindahl-Hirschman Index (HHI) Analysis for UPI Market Concentration.

HHI = Σ(si²) where si = market share of firm i (as decimal)

Interpretation:
- HHI < 0.15  → Competitive market
- 0.15 ≤ HHI ≤ 0.25 → Moderately concentrated
- HHI > 0.25  → Highly concentrated

US DOJ uses HHI for antitrust evaluation.
NPCI has proposed a 30% market share cap for UPI apps.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class HHIResult:
    period: str
    hhi: float
    interpretation: str
    top2_share: float
    equivalent_firms: float
    shares: Dict[str, float]


class HHIAnalyzer:
    """Computes and analyzes market concentration metrics."""

    def __init__(self):
        self.silver_path = Path("data/silver")
        self.output_path = Path("data/gold/exports")

    def run(self) -> bool:
        try:
            results = self.compute_hhi_timeseries()
            insights = self.generate_insights(results)
            self._save_results(results, insights)
            return True
        except Exception as e:
            logger.exception(f"HHI analysis failed: {e}")
            return False

    def compute_hhi_timeseries(self) -> List[HHIResult]:
        """Compute HHI for each available time period."""
        share_file = self.silver_path / "market_share" / "app_market_share.parquet"

        if not share_file.exists():
            logger.warning("Market share data not found")
            return []

        df = pd.read_parquet(share_file)
        results = []

        for (year, month), group in df.groupby(["year", "month"]):
            shares = dict(zip(group["app_name"], group["market_share_decimal"]))

            hhi = sum(s ** 2 for s in shares.values())

            if hhi > 0.25:
                interp = "Highly Concentrated"
            elif hhi > 0.15:
                interp = "Moderately Concentrated"
            else:
                interp = "Competitive"

            sorted_shares = sorted(shares.values(), reverse=True)
            top2 = sum(sorted_shares[:2]) * 100

            equiv = 1.0 / hhi if hhi > 0 else float("inf")

            results.append(HHIResult(
                period=f"{year}-{int(month):02d}",
                hhi=round(hhi, 4),
                interpretation=interp,
                top2_share=round(top2, 2),
                equivalent_firms=round(equiv, 1),
                shares=shares,
            ))

        return results

    def generate_insights(self, results: List[HHIResult]) -> Dict:
        """Generate key insights from HHI analysis."""
        if not results:
            return {}

        latest = results[-1]

        insights = {
            "current_hhi": latest.hhi,
            "current_interpretation": latest.interpretation,
            "top2_duopoly_share": latest.top2_share,
            "equivalent_firms": latest.equivalent_firms,
            "key_findings": [
                f"India's UPI market has an HHI of {latest.hhi:.4f}, "
                f"classified as '{latest.interpretation}'.",

                f"PhonePe and Google Pay together control {latest.top2_share:.1f}% "
                f"of all UPI transactions — effectively a duopoly.",

                f"The market behaves as if it has only {latest.equivalent_firms:.1f} "
                f"equal-sized competitors (equivalent firms metric).",

                f"NPCI's proposed 30% market share cap would require PhonePe to "
                f"shed ~{max(0, latest.shares.get('PhonePe', 0) * 100 - 30):.1f} "
                f"percentage points of market share.",

                "This level of concentration creates systemic risk: if PhonePe's "
                "infrastructure fails, nearly half of India's digital payments halt.",
            ],
            "policy_implications": [
                "NPCI should accelerate enforcement of the 30% cap",
                "New entrants (WhatsApp Pay, CRED) need regulatory support",
                "Interoperability must be maintained to prevent lock-in",
                "Backup routing infrastructure needed for systemic resilience",
            ],
        }

        return insights

    def _save_results(self, results: List[HHIResult], insights: Dict) -> None:
        """Save analysis results."""
        if results:
            df = pd.DataFrame([{
                "period": r.period,
                "hhi": r.hhi,
                "interpretation": r.interpretation,
                "top2_share": r.top2_share,
                "equivalent_firms": r.equivalent_firms,
            } for r in results])

            output_file = self.output_path / "hhi_analysis.parquet"
            self.output_path.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_file, index=False)
            logger.success(f"HHI analysis saved: {len(df)} periods")

            for finding in insights.get("key_findings", []):
                logger.info(f"📊 {finding}")
