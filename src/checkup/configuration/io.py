"""
Configuration file I/O and merging.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from checkup.configuration.env import (
    apply_naming_convention_overrides,
    substitute_env_vars,
)
from checkup.configuration.models import (
    CheckupConfig,
    MaterializerConfig,
    MetricConfig,
    ProviderConfig,
)

logger = logging.getLogger(__name__)

CONFIG_FILENAME = "checkup.yaml"
SCHEMA_FILENAME = "checkup.schema.json"


def load_yaml_file(path: Path) -> dict[str, Any]:
    """
    Load a single YAML file.
    """

    if not path.exists():
        return {}

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data if data else {}
    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML config %s: %s", path, e)
        raise


def find_config_files(start_dir: Path) -> list[Path]:
    """
    Find all checkup.yaml files from start_dir up to filesystem root.

    Returns:
        List of paths, ordered from root to start_dir (for merging)
    """

    config_files = []
    current = start_dir.resolve()

    while True:
        config_path = current / CONFIG_FILENAME
        if config_path.exists():
            config_files.append(config_path)

        parent = current.parent
        if parent == current:
            break
        current = parent

    return list(reversed(config_files))


def merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Merge two configuration dicts (override wins).
    """

    result = base.copy()

    for key, value in override.items():
        if key == "tags" and key in result:
            result[key] = {**result.get(key, {}), **value}
        elif key == "providers":
            result[key] = value
        elif key == "metrics":
            if key in result:

                def _metric_key(m: dict) -> tuple:
                    """
                    Key by (type, name) to allow multiple instances of same type
                    """

                    return (m.get("type"), m.get("name"))

                base_metrics = {_metric_key(m): m for m in result.get(key, [])}
                for metric in value:
                    base_metrics[_metric_key(metric)] = metric
                result[key] = list(base_metrics.values())
            else:
                result[key] = value
        else:
            result[key] = value

    return result


def parse_providers(raw: list[Any] | None) -> list[ProviderConfig]:
    """
    Parse provider configuration from raw YAML.

    Supports:
        - name: git
        - name: dbt
          project_dir: ./dbt
    """

    if not raw:
        return []

    providers = []
    for item in raw:
        if isinstance(item, str):
            providers.append(ProviderConfig(name=item))
        elif isinstance(item, dict):
            name = item.get("name")
            if name:
                config = {k: v for k, v in item.items() if k != "name"}
                providers.append(ProviderConfig(name=name, config=config))
    return providers


def parse_metrics(raw: list[Any] | None) -> list[MetricConfig]:
    """
    Parse metric configuration from raw YAML.

    Supports:
        - type: git_tracked_file_count
        - type: git_tracked_file_count
          name: cruft_file_exists
          pattern: ".cruft.json"
    """

    if not raw:
        return []

    metrics = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        metric_type = item.get("type")
        if not metric_type:
            continue
        name = item.get("name")
        config = {k: v for k, v in item.items() if k not in ("type", "name")}
        metrics.append(MetricConfig(type=metric_type, name=name, config=config))
    return metrics


def parse_materializer(raw: dict[str, Any] | None) -> MaterializerConfig | None:
    """
    Parse materializer configuration from raw YAML.
    """

    if not raw:
        return None

    raw_copy = raw.copy()
    mat_type = raw_copy.pop("type", None)
    if not mat_type:
        return None

    return MaterializerConfig(type=mat_type, config=raw_copy)


def load_config(
    config_path: Path | None = None,
    start_dir: Path | None = None,
) -> CheckupConfig:
    """
    Load checkup configuration with hierarchy and env var substitution.

    Resolution order:
    1. Find all checkup.yaml files from start_dir up to root
    2. Merge configs (child overrides parent)
    3. Apply naming convention env vars (CHECKUP__*)
    4. Substitute ${VAR} references

    Args:
        config_path: Explicit config file path (skips hierarchy search)
        start_dir: Directory to start searching from (defaults to cwd)

    Returns:
        Merged and resolved CheckupConfig
    """

    if config_path:
        raw = load_yaml_file(config_path)
    else:
        start = start_dir or Path.cwd()
        config_files = find_config_files(start)

        if not config_files:
            logger.debug("No config files found")
            return CheckupConfig.empty()

        raw = {}
        for cf in config_files:
            logger.debug("Loading config: %s", cf)
            file_config = load_yaml_file(cf)
            raw = merge_configs(raw, file_config)

    # Apply naming convention env vars first (lowest priority)
    raw = apply_naming_convention_overrides(raw)

    # Then substitute ${VAR} references (highest priority)
    raw = substitute_env_vars(raw)

    return CheckupConfig(
        tags=raw.get("tags", {}),
        providers=parse_providers(raw.get("providers")),
        metrics=parse_metrics(raw.get("metrics")),
        materializer=parse_materializer(raw.get("materializer")),
        select=raw.get("select"),
        exclude=raw.get("exclude"),
    )
