"""
Calculation state and skip/failure logic.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from checkup.errors import ProviderError
from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.provider import Provider

logger = logging.getLogger(__name__)


@dataclass
class CalculationState:
    """
    Tracks state during metric calculation.
    """

    context: dict[str, Any]
    tags: dict[str, Any]
    provided_classes: set[type[Provider]]
    failed_providers: dict[type[Provider], ProviderError]
    calculated: Measurements = field(default_factory=lambda: Measurements({}))
    skipped: set[type[Metric]] = field(default_factory=set)
    failed: set[type[Metric]] = field(default_factory=set)
    results: list[Measurement] = field(default_factory=list)


def should_skip(
    metric_cls: type[Metric],
    provided_classes: set[type[Provider]],
    skipped: set[type[Metric]],
) -> bool:
    """
    Check if a metric should be skipped due to missing providers or dependencies.
    """

    missing_providers = set(metric_cls.providers()) - provided_classes
    if missing_providers:
        logger.debug(
            "Skipping metric %s: missing providers %s",
            metric_cls.__name__,
            sorted(cls.name for cls in missing_providers),
        )
        return True

    skipped_deps = set(metric_cls.depends_on()) & skipped
    if skipped_deps:
        logger.debug(
            "Skipping metric %s: dependencies were skipped %s",
            metric_cls.__name__,
            sorted(cls.__name__ for cls in skipped_deps),
        )
        return True

    return False


def get_failed_dependencies(
    metric_cls: type[Metric],
    failed_providers: dict[type[Provider], ProviderError],
    failed_metrics: set[type[Metric]],
) -> list[str]:
    """
    Get list of failed provider/metric names that this metric depends on.
    """

    failed_names = []

    for provider_cls in metric_cls.providers():
        if provider_cls in failed_providers:
            failed_names.append(f"provider '{provider_cls.name}'")

    for dep_cls in metric_cls.depends_on():
        if dep_cls in failed_metrics:
            failed_names.append(f"metric '{dep_cls.__name__}'")

    return failed_names


def create_failed_measurement(
    metric: Metric,
    tags: dict[str, Any],
    failed_deps: list[str],
) -> Measurement:
    """
    Create a Measurement with null value due to failed dependencies.
    """

    diagnostic = f"Failed: {', '.join(failed_deps)} failed"
    logger.debug("Metric %s marked as failed: %s", metric.name, diagnostic)
    return Measurement(
        metric=metric,
        value=None,
        tags=dict(tags),
        diagnostic=diagnostic,
    )
