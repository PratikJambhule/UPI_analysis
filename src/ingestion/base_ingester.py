"""Abstract base class for all data ingesters."""

from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger
import yaml


class BaseIngester(ABC):
    """Abstract base class for all data ingesters."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.ingest_timestamp = datetime.utcnow().isoformat()
        self.config = self._load_config()
        logger.info(f"Initialized {source_name} ingester at {self.ingest_timestamp}")

    def _load_config(self) -> dict:
        with open("config/sources.yaml", "r") as f:
            sources = yaml.safe_load(f)
        return sources["sources"].get(self.source_name, {})

    @abstractmethod
    def extract(self) -> None:
        """Extract data from source to Bronze layer."""
        pass

    @abstractmethod
    def validate_extraction(self) -> bool:
        """Validate that extraction was successful."""
        pass

    def run(self) -> bool:
        """Execute the full ingestion pipeline."""
        try:
            logger.info(f"Starting extraction for {self.source_name}")
            self.extract()

            if self.validate_extraction():
                logger.success(f"✅ {self.source_name} ingestion complete")
                return True
            else:
                logger.error(f"❌ {self.source_name} validation failed")
                return False

        except Exception as e:
            logger.exception(f"💥 {self.source_name} ingestion failed: {e}")
            return False
