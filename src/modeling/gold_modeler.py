"""Gold Layer Modeler — Builds Star Schema in DuckDB from Silver Parquets."""

from pathlib import Path

import duckdb
from loguru import logger


class GoldModeler:
    """Builds Star Schema from Silver layer data into DuckDB."""

    def __init__(self):
        self.silver = Path("data/silver")
        self.gold = Path("data/gold")
        self.gold.mkdir(parents=True, exist_ok=True)
        self.db_path = self.gold / "upi_analytics.duckdb"
        self.con = duckdb.connect(str(self.db_path))

    def run(self) -> bool:
        """Build all dimension and fact tables."""
        try:
            self._build_dim_date()
            self._build_dim_geography()
            self._build_dim_app()
            self._build_dim_category()
            self._build_fact_transactions()
            self._build_fact_market_concentration()
            self._build_fact_cash_displacement()
            self._build_fact_digital_divide()
            self._create_analytical_views()
            self._export_gold_parquets()

            logger.success("✅ Gold layer Star Schema built successfully!")
            return True
        except Exception as e:
            logger.exception(f"Gold layer modeling failed: {e}")
            return False
        finally:
            self.con.close()

    # ── Dimension Tables ─────────────────────────────────────────────

    def _build_dim_date(self) -> None:
        self.con.execute("""
            CREATE OR REPLACE TABLE dim_date AS
            WITH date_spine AS (
                SELECT CAST(range AS DATE) AS full_date
                FROM range(DATE '2017-01-01', DATE '2027-01-01', INTERVAL 1 DAY)
            )
            SELECT
                CAST(strftime(full_date, '%Y%m%d') AS INTEGER) AS date_key,
                full_date,
                EXTRACT(YEAR FROM full_date)::INTEGER AS year,
                EXTRACT(QUARTER FROM full_date)::INTEGER AS quarter,
                EXTRACT(MONTH FROM full_date)::INTEGER AS month,
                strftime(full_date, '%B') AS month_name,

                -- Indian Fiscal Year (April–March)
                CASE WHEN EXTRACT(MONTH FROM full_date) >= 4
                    THEN 'FY' || EXTRACT(YEAR FROM full_date) || '-' ||
                         RIGHT(CAST(EXTRACT(YEAR FROM full_date) + 1 AS VARCHAR), 2)
                    ELSE 'FY' || (EXTRACT(YEAR FROM full_date) - 1) || '-' ||
                         RIGHT(CAST(EXTRACT(YEAR FROM full_date) AS VARCHAR), 2)
                END AS fiscal_year,

                CASE
                    WHEN EXTRACT(MONTH FROM full_date) BETWEEN 4 AND 6 THEN 'Q1'
                    WHEN EXTRACT(MONTH FROM full_date) BETWEEN 7 AND 9 THEN 'Q2'
                    WHEN EXTRACT(MONTH FROM full_date) BETWEEN 10 AND 12 THEN 'Q3'
                    ELSE 'Q4'
                END AS fiscal_quarter,

                -- Festival flags
                CASE WHEN EXTRACT(MONTH FROM full_date) IN (10,11,12,1,3) THEN TRUE
                     ELSE FALSE END AS is_festival_month,

                CASE
                    WHEN EXTRACT(MONTH FROM full_date) = 10 THEN 'Dussehra/Navratri'
                    WHEN EXTRACT(MONTH FROM full_date) = 11 THEN 'Diwali'
                    WHEN EXTRACT(MONTH FROM full_date) = 12 THEN 'Christmas'
                    WHEN EXTRACT(MONTH FROM full_date) = 1 THEN 'New Year'
                    WHEN EXTRACT(MONTH FROM full_date) = 3 THEN 'Holi/FY-End'
                    ELSE NULL
                END AS festival_name

            FROM date_spine
        """)
        count = self.con.execute("SELECT count(*) FROM dim_date").fetchone()[0]
        logger.info(f"dim_date: {count} rows (2017-01 to 2026-12)")

    def _build_dim_geography(self) -> None:
        district_file = str(self.silver / "geographic" / "district_transactions.parquet")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE dim_geography AS
            WITH districts AS (
                SELECT DISTINCT
                    state_clean AS state_name,
                    district_clean AS district_name,
                    region
                FROM read_parquet('{district_file}')
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY state_name, district_name)::INTEGER AS geo_key,
                state_name,
                district_name,
                region,
                CASE WHEN LOWER(district_name) IN (
                    'mumbai', 'delhi', 'bengaluru urban', 'bangalore urban',
                    'hyderabad', 'chennai', 'kolkata', 'pune', 'ahmedabad'
                ) THEN TRUE ELSE FALSE END AS is_metro
            FROM districts
        """)
        count = self.con.execute("SELECT count(*) FROM dim_geography").fetchone()[0]
        logger.info(f"dim_geography: {count} districts")

    def _build_dim_app(self) -> None:
        self.con.execute("""
            CREATE OR REPLACE TABLE dim_app AS
            SELECT * FROM (VALUES
                (1, 'PhonePe',      'Walmart/Flipkart',       2016, TRUE),
                (2, 'Google Pay',   'Google/Alphabet',         2017, TRUE),
                (3, 'Paytm',        'One97 Communications',    2017, TRUE),
                (4, 'CRED',         'CRED (Kunal Shah)',       2020, FALSE),
                (5, 'Amazon Pay',   'Amazon',                  2019, FALSE),
                (6, 'WhatsApp Pay',  'Meta',                    2022, FALSE),
                (7, 'Others',       'Various',                 NULL, FALSE)
            ) AS t(app_key, app_name, parent_company, launch_year, is_major_player)
        """)
        logger.info("dim_app: 7 apps")

    def _build_dim_category(self) -> None:
        self.con.execute("""
            CREATE OR REPLACE TABLE dim_category AS
            SELECT * FROM (VALUES
                (1, 'recharge_bill_payments', 'Recharge & Bill Payments', FALSE, TRUE),
                (2, 'p2p_payments',           'Peer-to-Peer Payments',    TRUE,  FALSE),
                (3, 'merchant_payments',      'Merchant Payments',        FALSE, TRUE),
                (4, 'financial_services',     'Financial Services',       FALSE, FALSE),
                (5, 'others',                 'Others',                   FALSE, FALSE)
            ) AS t(category_key, category_code, category_name, is_p2p, is_p2m)
        """)
        logger.info("dim_category: 5 categories")

    # ── Fact Tables ──────────────────────────────────────────────────

    def _build_fact_transactions(self) -> None:
        txn_file = str(self.silver / "transactions" / "phonepe_agg_transactions.parquet")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE fact_upi_transactions AS
            SELECT
                CAST(year * 10000 + ((quarter - 1) * 3 + 1) * 100 + 1 AS INTEGER) AS date_key,
                category_clean AS category,
                transaction_count AS txn_count,
                transaction_amount AS txn_amount_inr,
                avg_transaction_value AS avg_txn_value,
                year,
                quarter
            FROM read_parquet('{txn_file}')
        """)
        count = self.con.execute("SELECT count(*) FROM fact_upi_transactions").fetchone()[0]
        logger.info(f"fact_upi_transactions: {count} rows")

    def _build_fact_market_concentration(self) -> None:
        share_file = str(self.silver / "market_share" / "app_market_share.parquet")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE fact_market_concentration AS
            WITH shares AS (
                SELECT * FROM read_parquet('{share_file}')
            ),
            hhi_calc AS (
                SELECT
                    year, month,
                    SUM(POWER(market_share_decimal, 2)) AS hhi_index,
                    SUM(CASE WHEN app_name_clean IN ('PhonePe', 'Google Pay')
                         THEN market_share_pct ELSE 0 END) AS top2_combined_share,
                    COUNT(CASE WHEN market_share_pct > 1 THEN 1 END) AS num_apps_above_1pct
                FROM shares
                GROUP BY year, month
            )
            SELECT
                CAST(year * 10000 + month * 100 + 1 AS INTEGER) AS date_key,
                hhi_index,
                ROUND(hhi_index, 4) AS hhi_rounded,
                top2_combined_share,
                num_apps_above_1pct,
                CASE
                    WHEN hhi_index > 0.25 THEN 'Highly Concentrated'
                    WHEN hhi_index > 0.15 THEN 'Moderately Concentrated'
                    ELSE 'Competitive'
                END AS concentration_category,
                ROUND(1.0 / hhi_index, 1) AS equivalent_firms
            FROM hhi_calc
        """)
        count = self.con.execute("SELECT count(*) FROM fact_market_concentration").fetchone()[0]
        logger.info(f"fact_market_concentration: {count} rows")

    def _build_fact_cash_displacement(self) -> None:
        npci_file = str(self.silver / "transactions" / "npci_monthly_volumes.parquet")
        rbi_file = str(self.silver / "transactions" / "rbi_currency_circulation.parquet")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE fact_cash_displacement AS
            WITH upi AS (
                SELECT year, month,
                       transaction_volume_billions AS upi_volume_bn,
                       transaction_value_lakh_crores AS upi_value_lakh_cr
                FROM read_parquet('{npci_file}')
            ),
            cash AS (
                SELECT year, month,
                       currency_in_circulation_lakh_cr AS cic_lakh_cr
                FROM read_parquet('{rbi_file}')
            ),
            joined AS (
                SELECT
                    u.year, u.month,
                    u.upi_volume_bn,
                    u.upi_value_lakh_cr,
                    (SELECT c2.cic_lakh_cr FROM cash c2
                     WHERE c2.year = u.year AND c2.month <= u.month
                     ORDER BY c2.month DESC LIMIT 1) AS cic_lakh_cr
                FROM upi u
            )
            SELECT
                CAST(year * 10000 + month * 100 + 1 AS INTEGER) AS date_key,
                upi_volume_bn,
                upi_value_lakh_cr,
                cic_lakh_cr,
                ROUND(upi_value_lakh_cr / NULLIF(cic_lakh_cr, 0), 4)
                    AS digital_to_cash_ratio,
                upi_value_lakh_cr / NULLIF(cic_lakh_cr, 0) AS displacement_index
            FROM joined
            WHERE cic_lakh_cr IS NOT NULL
        """)
        count = self.con.execute("SELECT count(*) FROM fact_cash_displacement").fetchone()[0]
        logger.info(f"fact_cash_displacement: {count} rows")

    def _build_fact_digital_divide(self) -> None:
        district_file = str(self.silver / "geographic" / "district_transactions.parquet")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE fact_digital_divide AS
            WITH district_metrics AS (
                SELECT
                    year, quarter,
                    state_clean AS state,
                    district_clean AS district,
                    SUM(transaction_count) AS total_txn_count,
                    SUM(transaction_amount) AS total_txn_amount,
                    AVG(avg_transaction_value) AS avg_txn_value
                FROM read_parquet('{district_file}')
                GROUP BY year, quarter, state_clean, district_clean
            ),
            ranked AS (
                SELECT *,
                    PERCENT_RANK() OVER (
                        PARTITION BY year, quarter ORDER BY total_txn_count
                    ) AS national_percentile,
                    NTILE(4) OVER (
                        PARTITION BY year, quarter ORDER BY total_txn_count
                    ) AS adoption_quartile
                FROM district_metrics
            )
            SELECT
                CAST(year * 10000 + ((quarter - 1) * 3 + 1) * 100 + 1 AS INTEGER) AS date_key,
                state, district,
                total_txn_count, total_txn_amount, avg_txn_value,
                ROUND(national_percentile * 100, 1) AS national_percentile,
                CASE adoption_quartile
                    WHEN 1 THEN 'Very Low Adoption'
                    WHEN 2 THEN 'Low Adoption'
                    WHEN 3 THEN 'Medium Adoption'
                    WHEN 4 THEN 'High Adoption'
                END AS adoption_tier
            FROM ranked
        """)
        count = self.con.execute("SELECT count(*) FROM fact_digital_divide").fetchone()[0]
        logger.info(f"fact_digital_divide: {count} rows")

    # ── Analytical Views ─────────────────────────────────────────────

    def _create_analytical_views(self) -> None:
        self.con.execute("""
            CREATE OR REPLACE VIEW v_monthly_summary AS
            SELECT
                d.year, d.month, d.month_name, d.fiscal_year,
                d.is_festival_month, d.festival_name,
                SUM(f.txn_count) AS total_transactions,
                SUM(f.txn_amount_inr) AS total_value_inr,
                AVG(f.avg_txn_value) AS avg_transaction_value
            FROM fact_upi_transactions f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.year, d.month, d.month_name, d.fiscal_year,
                     d.is_festival_month, d.festival_name
            ORDER BY d.year, d.month
        """)

        self.con.execute("""
            CREATE OR REPLACE VIEW v_state_rankings AS
            SELECT
                state,
                (date_key / 10000)::INTEGER AS year,
                SUM(total_txn_count) AS annual_transactions,
                SUM(total_txn_amount) AS annual_value,
                COUNT(DISTINCT district) AS num_districts,
                AVG(CASE WHEN adoption_tier = 'Very Low Adoption'
                     THEN 1.0 ELSE 0.0 END) AS pct_underserved_districts,
                RANK() OVER (PARTITION BY (date_key / 10000)::INTEGER
                             ORDER BY SUM(total_txn_count) DESC) AS state_rank
            FROM fact_digital_divide
            GROUP BY state, (date_key / 10000)::INTEGER
        """)
        logger.info("Created views: v_monthly_summary, v_state_rankings")

    # ── Export ────────────────────────────────────────────────────────

    def _export_gold_parquets(self) -> None:
        """Export Gold tables as Parquet for Power BI / Streamlit."""
        export_path = self.gold / "exports"
        export_path.mkdir(parents=True, exist_ok=True)

        tables = [
            "dim_date", "dim_geography", "dim_app", "dim_category",
            "fact_upi_transactions", "fact_market_concentration",
            "fact_cash_displacement", "fact_digital_divide",
        ]

        for table in tables:
            try:
                df = self.con.execute(f"SELECT * FROM {table}").fetchdf()
                df.to_parquet(export_path / f"{table}.parquet", index=False)
                logger.info(f"  Exported {table}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"  Could not export {table}: {e}")

        # Also export views
        for view in ["v_monthly_summary", "v_state_rankings"]:
            try:
                df = self.con.execute(f"SELECT * FROM {view}").fetchdf()
                df.to_parquet(export_path / f"{view}.parquet", index=False)
                logger.info(f"  Exported {view}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"  Could not export {view}: {e}")
