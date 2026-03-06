"""CheckHub main orchestration."""

import logging
import os
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from checkup.config import load_config
from checkup.errors import DuplicateMetricNameError, MetricPicklingError, ProviderError
from checkup.executor import MetricCalculator, ProviderExecutor
from checkup.graph import build_dependency_graph, topological_sort
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
    """Result of measuring metrics.

    Contains all calculated metrics and any errors from failed contexts.
    """

    metrics: list[Metric]
    direct_metric_names: set[str] = Field(default_factory=set)
    errors: list[tuple[list[Provider], Exception]] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    def materialize(self, materializer: "Materializer") -> None:
        """Output results using materializer.

        Args:
            materializer: Materializer instance for output
        """
        materializer.materialize(self.metrics, self.direct_metric_names)


def _measure_single_provider_set(
    provider_set: list[Provider],
    execution_order: list[type[Metric]],
    metric_configs: dict,
) -> list[Metric]:
    """Calculate all metrics for a single provider set.

    This is a module-level function for ProcessPoolExecutor compatibility.

    Args:
        provider_set: List of provider instances
        execution_order: Topologically sorted metric classes
        metric_configs: Config dict for metrics

    Returns:
        List of calculated metrics with tags merged

    Raises:
        ProviderError: If a provider fails during execution
    """
    context, tags, errors = ProviderExecutor().execute(provider_set)
    failed_providers = {type(e.provider): e for e in errors}
    return MetricCalculator(metric_configs).calculate(
        execution_order,
        context,
        tags,
        {type(p) for p in provider_set},
        failed_providers,
    )


class CheckHub:
    """Main entry point for metrics calculation.

    Usage:
        CheckHub()
            .with_metrics([MetricA, MetricB])
            .measure()
            .materialize(ConsoleMaterializer())
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize CheckHub.

        Args:
            config_path: Optional path to YAML config file
        """
        self._metrics: list[type[Metric]] = []
        self._provider_sets: list[list[Provider]] = []
        self._config_path = config_path

    def with_metrics(self, metrics: Iterable[type[Metric]]) -> "CheckHub":
        """Register metrics to calculate.

        Args:
            metrics: Iterable of metric classes

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
            MeasurementResult containing all calculated metrics and errors

        Raises:
            DuplicateMetricNameError: If multiple metrics have the same name
        """
        logger.info(
            "Starting measurement with %d metrics and %d provider sets",
            len(self._metrics),
            len(self._provider_sets),
        )

        metric_configs: dict = {}
        if self._config_path:
            logger.debug("Loading config from %s", self._config_path)
            metric_configs = load_config(self._config_path)

        # Build dependency graph and get execution order
        logger.debug("Building dependency graph")
        execution_order = topological_sort(build_dependency_graph(self._metrics))

        # Validate unique metric names across all metrics (including dependencies)
        validate_unique_metric_names(list(execution_order))

        direct_metric_names = {m.name for m in self._metrics}

        # Use empty provider set if none specified and none required
        provider_sets = self._provider_sets if self._provider_sets else [[]]

        # Validate providers before running
        validate_providers(list(execution_order), provider_sets)

        all_metrics: list[Metric] = []
        all_errors: list[tuple[list[Provider], Exception]] = []
        workers = max_workers if max_workers is not None else os.cpu_count()

        logger.debug("Executing with %d workers", workers)
        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_provider_set = {
                executor.submit(
                    _measure_single_provider_set,
                    provider_set=ps,
                    execution_order=execution_order,
                    metric_configs=metric_configs,
                ): ps
                for ps in provider_sets
            }

            for future in as_completed(future_to_provider_set):
                ps = future_to_provider_set[future]
                try:
                    all_metrics.extend(future.result())
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
                "Measurement complete: %d metrics calculated, %d failed contexts:\n  %s",
                len(all_metrics),
                len(all_errors),
                failed_contexts_str,
            )
        else:
            logger.info(
                "Measurement complete: %d metrics calculated",
                len(all_metrics),
            )
        return MeasurementResult(
            metrics=all_metrics,
            direct_metric_names=direct_metric_names,
            errors=all_errors,
        )
