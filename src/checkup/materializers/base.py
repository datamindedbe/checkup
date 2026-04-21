"""Base materializer class and measurement grouping helpers."""

from abc import ABC, abstractmethod
from collections import defaultdict

from pydantic import BaseModel

from checkup.metric import Measurement


def group_measurements_by_tags(
    measurements: list[Measurement],
    tag1: str,
    tag2: str,
    default_value: str = "Unknown",
) -> dict[tuple[str, str], list[Measurement]]:
    """Group measurements by two tag values.

    Args:
        measurements: List of measurements to group
        tag1: First tag name for grouping
        tag2: Second tag name for grouping
        default_value: Value to use when tag is missing

    Returns:
        Dict mapping (tag1_value, tag2_value) tuples to measurement lists
    """
    groups: dict[tuple[str, str], list[Measurement]] = {}
    for measurement in measurements:
        tag1_value = measurement.tags.get(tag1, default_value)
        tag2_value = measurement.tags.get(tag2, default_value)
        key = (tag1_value, tag2_value)

        if key not in groups:
            groups[key] = []
        groups[key].append(measurement)

    return groups


def group_measurements_hierarchical(
    measurements: list[Measurement],
    tag1: str,
    tag2: str,
    default_value: str = "Ungrouped",
) -> dict[str, dict[str, list[Measurement]]]:
    """Group measurements hierarchically by two tag values.

    Args:
        measurements: List of measurements to group
        tag1: First tag name for top-level grouping
        tag2: Second tag name for nested grouping
        default_value: Value to use when tag is missing

    Returns:
        Nested dict: {tag1_value: {tag2_value: [measurements]}}
    """
    grouped: dict[str, dict[str, list[Measurement]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for measurement in measurements:
        group1_value = measurement.tags.get(tag1, default_value)
        group2_value = measurement.tags.get(tag2, default_value)
        grouped[group1_value][group2_value].append(measurement)

    return dict(grouped)


class Materializer(ABC, BaseModel):
    """Base class for measurement materializers.

    Materializers format and output measurements to various formats.

    Attributes:
        include_indirect: If True, include measurements that were auto-added as
            dependencies. If False (default), only include directly requested metrics.
    """

    include_indirect: bool = False

    def _filter_measurements(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> list[Measurement]:
        """Filter measurements based on include_indirect setting.

        Args:
            measurements: List of all calculated measurements
            direct_metric_names: Set of names of directly requested metrics

        Returns:
            Filtered list of measurements
        """
        if self.include_indirect:
            return measurements
        return [m for m in measurements if m.metric.name in direct_metric_names]

    @abstractmethod
    def materialize(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> None:
        """Format and output measurements.

        Args:
            measurements: List of calculated measurements
            direct_metric_names: Set of names of directly requested metrics
        """
        pass
