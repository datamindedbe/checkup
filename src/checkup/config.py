"""YAML configuration loading."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Exception raised when configuration loading fails."""

    def __init__(self, config_path: Path, original_error: Exception):
        self.config_path = config_path
        self.original_error = original_error
        super().__init__(
            f"Failed to load config from '{config_path}': {original_error}"
        )


def load_config(config_path: Path) -> dict[str, dict[str, Any]]:
    """Load metric configurations from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Dict mapping metric names to their config dicts
        Empty dict if file doesn't exist

    Raises:
        ConfigLoadError: If the file exists but cannot be parsed
    """
    if not config_path.exists():
        logger.debug("Config file does not exist: %s", config_path)
        return {}

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML config: %s", e)
        raise ConfigLoadError(config_path, e) from e

    if not data or "metrics" not in data:
        logger.debug("Config file has no 'metrics' section: %s", config_path)
        return {}

    metrics_config = data["metrics"]
    logger.debug(
        "Loaded config for %d metrics from %s",
        len(metrics_config),
        config_path,
    )
    return metrics_config
