"""Base materializer class."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from checkup.measurement import Measurement


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
