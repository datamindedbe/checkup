"""YAML configuration loading."""

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: Path) -> dict[str, dict[str, Any]]:
    """Load metric configurations from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Dict mapping metric names to their config dicts
        Empty dict if file doesn't exist
    """
    if not config_path.exists():
        return {}

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data or "metrics" not in data:
        return {}

    return data["metrics"]
