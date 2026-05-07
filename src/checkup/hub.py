"""CheckHub orchestration."""

import logging
import os
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from checkup.errors import DuplicateMetricNameError, MetricPicklingError, ProviderError
from checkup.executor import MetricCalculator, ProviderExecutor
from checkup.graph import build_dependency_graph, topological_sort
from checkup.measurement import Measurement
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.validators import validate_providers, validate_unique_metric_names

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from checkup.materializers import Materializer

# Re-export for backwards compatibility
__all__ = [
    "CheckHub",
    "MeasurementResult",
    "ProviderError",
    "MetricPicklingError",
    "DuplicateMetricNameError",
]


class MeasurementResult(BaseModel):
    """
    Result of measuring metrics.

    Contains all calculated measurements and any errors from failed contexts.
    """

    measurements: list[Measurement]
    direct_metric_names: set[str] = Field(default_factory=set)
    errors: list[tuple[list[Provider], Exception]] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    def materialize(self, materializer: "Materializer") -> None:
        """Output results using materializer.

        Args:
            materializer: Materializer instance for output
        """
        materializer.materialize(self.measurements, self.direct_metric_names)


def _measure_single_provider_set(
    provider_set: list[Provider],
    metrics: list[Metric],
    execution_order: list[type[Metric]],
) -> list[Measurement]:
    """Calculate all metrics for a single provider set.

    This is a module-level function for ProcessPoolExecutor compatibility.

    Args:
        provider_set: List of provider instances
        metrics: List of metric instances to calculate
        execution_order: Topologically sorted metric classes

    Returns:
        List of Measurements with tags merged

    Raises:
        ProviderError: If a provider fails during execution
    """

    context, tags, errors = ProviderExecutor().execute(provider_set)
    failed_providers = {type(e.provider): e for e in errors}

    return MetricCalculator().calculate(
        metrics,
        execution_order,
        context,
        tags,
        {type(p) for p in provider_set},
        failed_providers,
    )


class CheckHub:
    """
    Main entry point for metrics calculation.

    Usage:
        CheckHub()
            .with_metrics([MetricA(), MetricB(threshold=10)])
            .measure()
            .materialize(ConsoleMaterializer())
    """

    def __init__(self) -> None:
        """Initialize CheckHub."""
        self._metrics: list[Metric] = []
        self._provider_sets: list[list[Provider]] = []

    def with_metrics(self, metrics: Iterable[Metric]) -> "CheckHub":
        """Register metric instances to calculate.

        Args:
            metrics: Iterable of metric instances (configured via constructor)

        Returns:
            Self for chaining
        """
        self._metrics.extend(metrics)
        return self

    def with_providers(self, provider_sets: Iterable[Iterable[Provider]]) -> "CheckHub":
        """Register provider sets to run metrics against.

        Each inner iterable is a set of providers for one measurement run.
        Metrics are calculated once per provider set.

        Args:
            provider_sets: Iterable of provider sets

        Returns:
            Self for chaining
        """
        for provider_set in provider_sets:
            self._provider_sets.append(list(provider_set))
        return self

    def measure(
        self,
        max_workers: int | None = None,
    ) -> MeasurementResult:
        """Execute the measurement pipeline.

        Args:
            max_workers: Max parallel workers. None = use all CPUs.

        Returns:
            MeasurementResult containing all calculated measurements and errors

        Raises:
            DuplicateMetricNameError: If multiple metrics have the same name
        """
        logger.info(
            "Starting measurement with %d metrics and %d provider sets",
            len(self._metrics),
            len(self._provider_sets),
        )

        metric_classes = [type(m) for m in self._metrics]
        logger.debug("Building dependency graph")
        execution_order = topological_sort(build_dependency_graph(metric_classes))
        validate_unique_metric_names(self._metrics)
        direct_metric_names = {m.name for m in self._metrics}
        provider_sets = self._provider_sets if self._provider_sets else [[]]
        validate_providers(list(execution_order), provider_sets)

        all_measurements: list[Measurement] = []
        all_errors: list[tuple[list[Provider], Exception]] = []
        workers = max_workers if max_workers is not None else os.cpu_count()

        logger.debug("Executing with %d workers", workers)
        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_provider_set = {
                executor.submit(
                    _measure_single_provider_set,
                    provider_set=ps,
                    metrics=self._metrics,
                    execution_order=execution_order,
                ): ps
                for ps in provider_sets
            }

            for future in as_completed(future_to_provider_set):
                ps = future_to_provider_set[future]
                try:
                    all_measurements.extend(future.result())
                except Exception as e:
                    logger.error("Provider set failed: %s", e)
                    logger.debug("Provider set failure details:", exc_info=True)
                    all_errors.append((ps, e))

        if all_errors:
            failed_contexts = []
            for ps, _ in all_errors:
                tags = {
                    k: v
                    for p in ps
                    if p.is_tag_provider()
                    for k, v in p.provide().items()
                }
                failed_contexts.append(
                    tags if tags else {"providers": [p.name for p in ps]}
                )
            failed_contexts_str = "\n  ".join(str(ctx) for ctx in failed_contexts)
            logger.info(
                "Measurement complete: %d measurements, %d failed contexts:\n  %s",
                len(all_measurements),
                len(all_errors),
                failed_contexts_str,
            )
        else:
            logger.info(
                "Measurement complete: %d measurements",
                len(all_measurements),
            )
        return MeasurementResult(
            measurements=all_measurements,
            direct_metric_names=direct_metric_names,
            errors=all_errors,
        )
