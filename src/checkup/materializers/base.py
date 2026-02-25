"""Base materializer class and metric grouping helpers."""

from abc import ABC, abstractmethod
from collections import defaultdict

from pydantic import BaseModel

from checkup.metric import Metric


def group_metrics_by_tags(
    metrics: list[Metric],
    tag1: str,
    tag2: str,
    default_value: str = "Unknown",
) -> dict[tuple[str, str], list[Metric]]:
    """Group metrics by two tag values.

    Args:
        metrics: List of metrics to group
        tag1: First tag name for grouping
        tag2: Second tag name for grouping
        default_value: Value to use when tag is missing

    Returns:
        Dict mapping (tag1_value, tag2_value) tuples to metric lists
    """
    groups: dict[tuple[str, str], list[Metric]] = {}
    for metric in metrics:
        tag1_value = metric.tags.get(tag1, default_value)
        tag2_value = metric.tags.get(tag2, default_value)
        key = (tag1_value, tag2_value)

        if key not in groups:
            groups[key] = []
        groups[key].append(metric)

    return groups


def group_metrics_hierarchical(
    metrics: list[Metric],
    tag1: str,
    tag2: str,
    default_value: str = "Ungrouped",
) -> dict[str, dict[str, list[Metric]]]:
    """Group metrics hierarchically by two tag values.

    Args:
        metrics: List of metrics to group
        tag1: First tag name for top-level grouping
        tag2: Second tag name for nested grouping
        default_value: Value to use when tag is missing

    Returns:
        Nested dict: {tag1_value: {tag2_value: [metrics]}}
    """
    grouped: dict[str, dict[str, list[Metric]]] = defaultdict(lambda: defaultdict(list))

    for metric in metrics:
        group1_value = metric.tags.get(tag1, default_value)
        group2_value = metric.tags.get(tag2, default_value)
        grouped[group1_value][group2_value].append(metric)

    return dict(grouped)


class Materializer(ABC, BaseModel):
    """Base class for metric materializers.

    Materializers format and output metrics to various formats.

    Attributes:
        include_indirect: If True, include metrics that were auto-added as
            dependencies. If False (default), only include directly requested metrics.
    """

    include_indirect: bool = False

    def _filter_metrics(
        self, metrics: list[Metric], direct_metric_names: set[str]
    ) -> list[Metric]:
        """Filter metrics based on include_indirect setting.

        Args:
            metrics: List of all calculated metrics
            direct_metric_names: Set of names of directly requested metrics

        Returns:
            Filtered list of metrics
        """
        if self.include_indirect:
            return metrics
        return [m for m in metrics if m.name in direct_metric_names]

    @abstractmethod
    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Format and output metrics.

        Args:
            metrics: List of calculated metrics
            direct_metric_names: Set of names of directly requested metrics
        """
        pass
