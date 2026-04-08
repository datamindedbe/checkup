"""
Environment variable handling for configuration.
"""

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)


def substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitute ${VAR} patterns with environment variables.

    Supports:
    - ${VAR} - substitute with env var value
    - ${VAR:-default} - substitute with default if VAR not set

    Args:
        value: Value to process (string, dict, list, or other)

    Returns:
        Value with environment variables substituted
    """

    if isinstance(value, str):
        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

        def replace(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            env_value = os.environ.get(var_name)
            if env_value is not None:
                return env_value
            if default is not None:
                return default
            logger.warning("Environment variable %s not found", var_name)
            return match.group(0)

        return re.sub(pattern, replace, value)

    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]

    return value


def apply_naming_convention_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """
    Apply CHECKUP__* environment variable overrides.

    Environment variables like CHECKUP__MATERIALIZER__SQLALCHEMY__CONNECTION_URL
    override corresponding config values (only if not already set).

    Args:
        config: Configuration dict to apply overrides to

    Returns:
        Configuration with environment variable overrides applied
    """

    prefix = "CHECKUP__"

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        parts = key[len(prefix) :].lower().split("__")
        if len(parts) < 2:
            continue

        section = parts[0]

        if section == "materializer" and len(parts) >= 3:
            _apply_materializer_override(config, parts, value, key)

        elif section == "provider" and len(parts) >= 3:
            _apply_provider_override(config, parts, value, key)

    return config


def _apply_materializer_override(
    config: dict[str, Any],
    parts: list[str],
    value: str,
    key: str,
) -> None:
    """
    Apply a materializer config override from env var.
    """

    materializer_type = parts[1]
    config_key = "_".join(parts[2:])

    if "materializer" not in config:
        return

    mat_type = config.get("materializer", {}).get("type", "")
    if mat_type and mat_type.lower() == materializer_type:
        if config_key not in config["materializer"]:
            config["materializer"][config_key] = value
            logger.debug("Applied env override: %s", key)


def _apply_provider_override(
    config: dict[str, Any],
    parts: list[str],
    value: str,
    key: str,
) -> None:
    """
    Apply a provider config override from env var.
    """

    provider_name = parts[1]
    config_key = "_".join(parts[2:])

    if "providers" not in config:
        return

    for provider in config["providers"]:
        if isinstance(provider, dict):
            name = list(provider.keys())[0] if provider else None
            if name and name.lower() == provider_name:
                if provider[name] is None:
                    provider[name] = {}
                if config_key not in provider.get(name, {}):
                    provider[name][config_key] = value
                    logger.debug("Applied env override: %s", key)
