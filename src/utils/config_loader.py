"""YAML configuration loader."""

from pathlib import Path
import yaml


def load_config(config_path: str = "config/settings.yaml") -> dict:
    """Load and return YAML configuration."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_sources(sources_path: str = "config/sources.yaml") -> dict:
    """Load data source configuration."""
    path = Path(sources_path)
    if not path.exists():
        raise FileNotFoundError(f"Sources config not found: {sources_path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)
