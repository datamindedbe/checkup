"""Validation functions for the Checkup framework."""

import logging
import pickle

from checkup.errors import DuplicateMetricNameError, MetricPicklingError
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.providers.tags import TagProvider

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


def validate_unique_metric_names(metrics: list[Metric]) -> None:
    """
    Validate that all metric instances have unique names.

    Args:
        metrics: List of metric instances to validate

    Raises:
        DuplicateMetricNameError: If multiple metrics share the same name
    """

    name_to_metrics: dict[str, list[Metric]] = {}
    for metric in metrics:
        name = metric.name
        if name not in name_to_metrics:
            name_to_metrics[name] = []
        name_to_metrics[name].append(metric)

    duplicates = {
        name: instances
        for name, instances in name_to_metrics.items()
        if len(instances) > 1
    }
    if duplicates:
        # Report the first duplicate found
        name, instances = next(iter(duplicates.items()))
        raise DuplicateMetricNameError(name, [type(m) for m in instances])


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
    """
    Validate all required providers are present in each provider set.

    Logs a warning for any missing providers instead of failing.

    Args:
        metrics: List of metric classes to check
        provider_sets: List of provider instance lists to validate
    """
    required = collect_required_providers(metrics)

    if not required:
        return

    for i, provider_set in enumerate(provider_sets):
        provided_classes = {type(p) for p in provider_set}
        missing = required - provided_classes

        if missing:
            # Try to identify the provider set using TagProvider tags if available
            # for more informative logging
            tag_provider = next(
                (p for p in provider_set if isinstance(p, TagProvider)), None
            )
            if tag_provider and tag_provider.tags:
                tags_str = ", ".join(f"{k}={v}" for k, v in tag_provider.tags.items())
                provider_set_desc = f"Provider set ({tags_str})"
            else:
                provider_set_desc = f"Provider set {i}"

            logger.warning(
                f"{provider_set_desc} is missing required providers: {', '.join(sorted(cls.name for cls in missing))}"
            )
