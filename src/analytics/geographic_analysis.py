"""
Geographic Digital Divide Analysis.
Identifies which districts/states are digitally excluded from UPI.

Metrics:
1. State-level Gini coefficient (intra-state inequality)
2. K-Means clustering of districts by adoption patterns
3. Bottom 50 underserved districts identification
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class DigitalDivideAnalyzer:
    """Analyzes geographic disparities in UPI adoption."""

    def __init__(self):
        self.silver_path = Path("data/silver")
        self.output_path = Path("data/gold/exports")

    def run(self) -> bool:
        try:
            district_df = self._load_district_data()
            if district_df is None:
                return True

            state_analysis = self._analyze_state_level(district_df)
            district_clusters = self._cluster_districts(district_df)
            underserved = self._identify_underserved(district_df)

            self._save_results(state_analysis, district_clusters, underserved)
            return True
        except Exception as e:
            logger.exception(f"Geographic analysis failed: {e}")
            return False

    def _load_district_data(self) -> pd.DataFrame:
        district_file = self.silver_path / "geographic" / "district_transactions.parquet"
        if not district_file.exists():
            logger.warning("District data not found")
            return None
        return pd.read_parquet(district_file)

    def _get_latest_period(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get the latest quarter's data."""
        latest_year = df["year"].max()
        latest_q = df[df["year"] == latest_year]["quarter"].max()
        return df[(df["year"] == latest_year) & (df["quarter"] == latest_q)]

    def _analyze_state_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute state-level UPI adoption metrics with Gini coefficient."""
        latest = self._get_latest_period(df)

        state_metrics = (
            latest
            .groupby("state_clean")
            .agg(
                total_transactions=("transaction_count", "sum"),
                total_value=("transaction_amount", "sum"),
                num_districts=("district_clean", "nunique"),
                avg_txn_per_district=("transaction_count", "mean"),
                median_txn_per_district=("transaction_count", "median"),
                min_district_txn=("transaction_count", "min"),
                max_district_txn=("transaction_count", "max"),
            )
            .reset_index()
        )

        def gini(values):
            """Compute Gini coefficient for inequality measurement."""
            sorted_vals = np.sort(values)
            n = len(sorted_vals)
            if n == 0 or np.sum(sorted_vals) == 0:
                return 0.0
            index = np.arange(1, n + 1)
            return float(
                (2 * np.sum(index * sorted_vals) / (n * np.sum(sorted_vals)))
                - (n + 1) / n
            )

        gini_by_state = (
            latest
            .groupby("state_clean")["transaction_count"]
            .apply(gini)
            .reset_index()
            .rename(columns={"transaction_count": "intra_state_gini"})
        )

        state_metrics = state_metrics.merge(gini_by_state, on="state_clean")
        state_metrics = state_metrics.sort_values("total_transactions", ascending=False)
        state_metrics["rank"] = range(1, len(state_metrics) + 1)

        logger.info(f"State analysis: {len(state_metrics)} states/UTs")
        logger.info(f"  Most digital: {state_metrics.iloc[0]['state_clean']}")
        logger.info(f"  Least digital: {state_metrics.iloc[-1]['state_clean']}")

        highest_gini_idx = gini_by_state["intra_state_gini"].idxmax()
        logger.info(f"  Highest intra-state inequality: "
                    f"{gini_by_state.loc[highest_gini_idx, 'state_clean']} "
                    f"(Gini={gini_by_state.loc[highest_gini_idx, 'intra_state_gini']:.3f})")

        return state_metrics

    def _cluster_districts(self, df: pd.DataFrame) -> pd.DataFrame:
        """K-Means clustering of districts by UPI adoption patterns."""
        latest = self._get_latest_period(df)

        district_features = (
            latest
            .groupby(["state_clean", "district_clean"])
            .agg(
                total_txn=("transaction_count", "sum"),
                total_value=("transaction_amount", "sum"),
                avg_txn_value=("avg_transaction_value", "mean"),
            )
            .reset_index()
        )

        features = district_features[["total_txn", "total_value", "avg_txn_value"]].fillna(0)
        features_log = np.log1p(features)

        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_log)

        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        district_features["cluster"] = kmeans.fit_predict(features_scaled)

        # Label clusters by median transaction volume (ascending)
        cluster_medians = district_features.groupby("cluster")["total_txn"].median()
        sorted_clusters = cluster_medians.sort_values().index.tolist()

        tier_labels = ["Very Low Adoption", "Low Adoption", "Medium Adoption", "High Adoption"]
        label_map = {c: tier_labels[i] for i, c in enumerate(sorted_clusters)}
        district_features["adoption_tier"] = district_features["cluster"].map(label_map)

        for tier in tier_labels:
            count = (district_features["adoption_tier"] == tier).sum()
            logger.info(f"  {tier}: {count} districts")

        return district_features

    def _identify_underserved(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify bottom 50 districts with lowest UPI penetration."""
        latest = self._get_latest_period(df)

        bottom_districts = (
            latest
            .groupby(["state_clean", "district_clean"])
            .agg(total_txn=("transaction_count", "sum"))
            .reset_index()
            .nsmallest(50, "total_txn")
        )

        logger.info(f"Bottom 50 underserved districts identified")
        for _, row in bottom_districts.head(5).iterrows():
            logger.info(f"  {row['district_clean']}, {row['state_clean']}: "
                        f"{row['total_txn']:,} transactions")

        return bottom_districts

    def _save_results(self, state_df, cluster_df, underserved_df):
        self.output_path.mkdir(parents=True, exist_ok=True)

        if state_df is not None:
            state_df.to_parquet(self.output_path / "state_analysis.parquet", index=False)
        if cluster_df is not None:
            cluster_df.to_parquet(self.output_path / "district_clusters.parquet", index=False)
        if underserved_df is not None:
            underserved_df.to_parquet(self.output_path / "underserved_districts.parquet", index=False)

        logger.success("Geographic analysis saved")
