"""Measurement and Measurements classes."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, overload

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from checkup.metric import Metric


class Measurement(BaseModel):
    """
    Result of a metric calculation.
    """

    metric: Metric
    value: Any = None
    tags: dict = Field(default_factory=dict)
    diagnostic: str = ""


class Measurements(Mapping[type["Metric"], Sequence["Measurement"]]):
    """
    Mapping from metrics to their measurements.

    Example usage:

        # Get all measurements for a metric
        all_measurements = measurements[MyMetric]

        # Get a single measurement
        measurement = measurements.get(MyMetric)

        # Get a measurement by name
        measurement = measurements.get(MyMetric, name="my_metric_instance")
    """

    def __init__(self, data: dict[type[Metric], Sequence[Measurement]] | None = None):
        self._data: dict[type[Metric], list[Measurement]] = defaultdict(list)
        if data:
            for metric_cls, measurements in data.items():
                self._data[metric_cls] = list(measurements)

    def __getitem__(self, metric_cls: type[Metric]) -> Sequence[Measurement]:
        return self._data.get(metric_cls, [])

    def __iter__(self) -> Iterator[type[Metric]]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, metric_cls: object) -> bool:
        return metric_cls in self._data and len(self._data[metric_cls]) > 0

    @overload
    def get(self, metric_cls: type[Metric]) -> Measurement | None: ...

    @overload
    def get(self, metric_cls: type[Metric], *, name: str) -> Measurement | None: ...

    def get(
        self, metric_cls: type[Metric], *, name: str | None = None
    ) -> Measurement | None:
        """
        Get a measurement, optionally filtered by metric name.

        Args:
            metric_cls: The metric class to look up
            name: Optional metric name to filter by

        Returns:
            The matching Measurement, or None if not found.
            Raises ValueError if multiple matches found.
        """

        results = self._data.get(metric_cls, [])
        if name is not None:
            results = [m for m in results if m.metric.name == name]

        if len(results) == 0:
            return None
        if len(results) > 1:
            raise ValueError(
                f"Multiple measurements match for {metric_cls.__name__}"
                + (f" with name '{name}'" if name else "")
            )

        return results[0]

    def append(self, metric_cls: type[Metric], measurement: Measurement) -> None:
        self._data[metric_cls].append(measurement)
