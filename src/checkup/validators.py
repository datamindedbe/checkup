"""Validation functions for the Checkup framework."""

import logging
import pickle

from checkup.errors import DuplicateMetricNameError, MetricPicklingError
from checkup.metric import Metric
from checkup.provider import Provider

logger = logging.getLogger(__name__)


def validate_pickleable(metric_cls: type[Metric]) -> None:
    """Validate that a metric class can be pickled.

    Args:
        metric_cls: Metric class to validate

    Raises:
        MetricPicklingError: If the metric cannot be pickled
    """
    try:
        # Try to pickle the class itself
        pickle.dumps(metric_cls)
    except (pickle.PicklingError, TypeError, AttributeError) as e:
        raise MetricPicklingError(metric_cls, e) from e


def validate_unique_metric_names(metrics: list[type[Metric]]) -> None:
    """Validate that all metrics have unique names.

    Args:
        metrics: List of metric classes to validate

    Raises:
        DuplicateMetricNameError: If multiple metrics share the same name
    """
    name_to_classes: dict[str, list[type[Metric]]] = {}
    for metric_cls in metrics:
        name = metric_cls.name
        if name not in name_to_classes:
            name_to_classes[name] = []
        name_to_classes[name].append(metric_cls)

    duplicates = {
        name: classes for name, classes in name_to_classes.items() if len(classes) > 1
    }
    if duplicates:
        # Report the first duplicate found
        name, classes = next(iter(duplicates.items()))
        raise DuplicateMetricNameError(name, classes)


def collect_required_providers(metrics: list[type[Metric]]) -> set[type[Provider]]:
    """Collect all required provider classes from metrics.

    Args:
        metrics: List of metric classes

    Returns:
        Set of required provider classes
    """
    required: set[type[Provider]] = set()
    for metric_cls in metrics:
        required.update(metric_cls.providers())
    return required


def validate_providers(
    metrics: list[type[Metric]],
    provider_sets: list[list[Provider]],
) -> None:
    """Validate all required providers are present in each provider set.

    Logs a warning for any missing providers instead of failing.

    Args:
        metrics: List of metric classes to check
        provider_sets: List of provider instance lists to validate
    """
    required = collect_required_providers(metrics)

    if not required:
        return  # No providers required

    for i, provider_set in enumerate(provider_sets):
        provided_classes = {type(p) for p in provider_set}
        missing = required - provided_classes

        if missing:
            logger.warning(
                "Provider set %d is missing required providers: %s",
                i,
                sorted(cls.name for cls in missing),
            )
