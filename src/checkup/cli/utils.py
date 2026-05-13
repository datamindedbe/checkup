"""
CLI utility functions.
"""

import logging

from checkup.configuration import CheckupConfig, MetricConfig, ProviderConfig

logger = logging.getLogger(__name__)


def apply_cli_overrides(
    cfg: CheckupConfig,
    tags: list[str] | None,
    providers: list[str] | None,
    metrics: list[str] | None,
) -> CheckupConfig:
    """
    Apply CLI flag overrides to config.

    When CLI arguments are provided, they replace the config file values
    """

    if tags:
        new_tags = {}
        for t in tags:
            if "=" in t:
                key, value = t.split("=", 1)
                new_tags[key] = value
    else:
        new_tags = dict(cfg.tags)

    if providers:
        new_providers = []
        for p in providers:
            name, config = parse_cli_item(p)
            new_providers.append(ProviderConfig(name=name, config=config))
    else:
        new_providers = list(cfg.providers)

    if metrics:
        new_metrics = []
        for m in metrics:
            metric_type, config = parse_cli_item(m)
            new_metrics.append(MetricConfig(type=metric_type, config=config))
    else:
        new_metrics = list(cfg.metrics)

    return CheckupConfig(
        tags=new_tags,
        providers=new_providers,
        metrics=new_metrics,
        materializer=cfg.materializer,
    )


def parse_cli_item(item: str) -> tuple[str, dict]:
    """
    Parse CLI item like 'name' or 'name:key=value,key2=value2'.
    """

    if ":" not in item:
        return item, {}

    name, config_str = item.split(":", 1)
    config: dict[str, str] = {}

    for pair in config_str.split(","):
        if "=" not in pair:
            logger.warning("Ignoring malformed config pair %r in %r", pair, item)
            continue
        key, value = pair.split("=", 1)
        config[key] = value

    return name, config
