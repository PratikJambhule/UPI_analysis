"""
Pipeline Orchestrator — Coordinates all ETL + Analytics stages.

Stages:
  1. INGEST    → Bronze layer (raw data from all sources)
  2. TRANSFORM → Silver layer (clean, validate, standardize)
  3. MODEL     → Gold layer (star schema, DuckDB)
  4. ANALYZE   → Run all analytical modules
"""

from datetime import datetime
from loguru import logger


class PipelineOrchestrator:
    """Orchestrates the full ETL + Analytics pipeline."""

    VALID_STAGES = ["ingest", "transform", "model", "analyze", "all"]

    def __init__(self):
        self.run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        logger.add(
            f"logs/pipeline_{self.run_id}.log",
            rotation="50 MB",
            level="DEBUG",
        )
        logger.info(f"Pipeline initialized | Run ID: {self.run_id}")

    def run_stage(self, stage: str) -> bool:
        """Run a specific pipeline stage."""
        stages = {
            "ingest": self._run_ingestion,
            "transform": self._run_transformation,
            "model": self._run_modeling,
            "analyze": self._run_analytics,
            "all": self._run_all,
        }

        if stage not in stages:
            logger.error(f"Unknown stage: {stage}. Valid: {self.VALID_STAGES}")
            return False

        return stages[stage]()

    def _run_ingestion(self) -> bool:
        """Execute all ingesters → Bronze layer."""
        logger.info("=" * 60)
        logger.info("STAGE 1: INGESTION (→ Bronze Layer)")
        logger.info("=" * 60)

        from src.ingestion.phonepe_pulse_ingester import PhonePePulseIngester
        from src.ingestion.npci_ingester import NPCIIngester
        from src.ingestion.rbi_ingester import RBIIngester

        results = {}

        pp = PhonePePulseIngester()
        results["phonepe_pulse"] = pp.run()

        npci = NPCIIngester()
        results["npci"] = npci.run()

        rbi = RBIIngester()
        results["rbi"] = rbi.run()

        for source, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"  {status} {source}")

        return all(results.values())

    def _run_transformation(self) -> bool:
        """Clean and validate → Silver layer."""
        logger.info("=" * 60)
        logger.info("STAGE 2: TRANSFORMATION (Bronze → Silver)")
        logger.info("=" * 60)

        try:
            from src.transformation.silver_transformer import SilverTransformer
            transformer = SilverTransformer()
            return transformer.run()
        except ImportError:
            logger.warning("SilverTransformer not yet implemented — skipping")
            return False

    def _run_modeling(self) -> bool:
        """Build star schema → Gold layer."""
        logger.info("=" * 60)
        logger.info("STAGE 3: MODELING (Silver → Gold)")
        logger.info("=" * 60)

        try:
            from src.modeling.gold_modeler import GoldModeler
            modeler = GoldModeler()
            return modeler.run()
        except ImportError:
            logger.warning("GoldModeler not yet implemented — skipping")
            return False

    def _run_analytics(self) -> bool:
        """Run all analytical modules."""
        logger.info("=" * 60)
        logger.info("STAGE 4: ANALYTICS")
        logger.info("=" * 60)

        results = {}

        try:
            from src.analytics.market_concentration import HHIAnalyzer
            results["market_concentration"] = HHIAnalyzer().run()
        except ImportError:
            logger.warning("HHIAnalyzer not yet implemented")
            results["market_concentration"] = False

        try:
            from src.analytics.forecasting import UPIForecaster
            results["forecasting"] = UPIForecaster().run()
        except ImportError:
            logger.warning("UPIForecaster not yet implemented")
            results["forecasting"] = False

        try:
            from src.analytics.geographic_analysis import DigitalDivideAnalyzer
            results["geographic"] = DigitalDivideAnalyzer().run()
        except ImportError:
            logger.warning("DigitalDivideAnalyzer not yet implemented")
            results["geographic"] = False

        try:
            from src.analytics.cash_displacement import CashDisplacementAnalyzer
            results["cash_displacement"] = CashDisplacementAnalyzer().run()
        except ImportError:
            logger.warning("CashDisplacementAnalyzer not yet implemented")
            results["cash_displacement"] = False

        for name, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"  {status} {name}")

        return all(results.values())

    def _run_all(self) -> bool:
        """Execute full pipeline end-to-end."""
        stages = [
            self._run_ingestion,
            self._run_transformation,
            self._run_modeling,
            self._run_analytics,
        ]

        for stage_fn in stages:
            if not stage_fn():
                logger.error(f"Pipeline failed at {stage_fn.__name__}")
                return False

        logger.success("🎉 Full pipeline completed successfully!")
        return True
