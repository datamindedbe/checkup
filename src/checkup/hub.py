"""CheckHub main orchestration."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from pydantic import BaseModel, Field

from checkup.config import load_config
from checkup.graph import build_dependency_graph, topological_sort
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context

if TYPE_CHECKING:
    from checkup.materializers import Materializer


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

    def with_providers(
        self, provider_sets: Iterable[Iterable[Provider]]
    ) -> "CheckHub":
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



    def _validate_providers(
        self,
        metrics: list[type[Metric]],
        provider_sets: list[list[Provider]],
    ) -> None:
        """Validate all required providers are present in each provider set.

        Args:
            metrics: List of metric classes to check
            provider_sets: List of provider instance lists to validate

        Raises:
            ValueError: If any required provider is missing from a provider set
        """
        # Collect all required provider classes from metrics
        required: set[type[Provider]] = set()
        for metric_cls in metrics:
            required.update(metric_cls.providers())

        if not required:
            return  # No providers required

        # Check each provider set
        for i, provider_set in enumerate(provider_sets):
            provided_classes = {type(p) for p in provider_set}
            missing = required - provided_classes

            if missing:
                missing_names = sorted(cls.name for cls in missing)
                raise ValueError(
                    f"Provider set {i} is missing required providers: {missing_names}"
                )

    def _execute_providers(
        self,
        provider_set: list[Provider],
    ) -> tuple[Context, dict[str, Any]]:
        """Execute all providers and build namespaced context.

        Each provider's data is added under its namespace (provider.name).
        TagProvider data is returned separately for merging into tags.

        Args:
            provider_set: List of provider instances

        Returns:
            Tuple of (context dict, tags dict)
        """
        from checkup.providers.tags import TagProvider

        context: Context = {}
        tags: dict[str, Any] = {}

        for provider in provider_set:
            data = provider.provide()
            if isinstance(provider, TagProvider):
                tags.update(data)
            else:
                context[provider.name] = data

        return context, tags

    def _measure_single_provider_set(
        self,
        provider_set: list[Provider],
        execution_order: list[type[Metric]],
        metric_configs: dict,
    ) -> list[Metric]:
        """Calculate all metrics for a single provider set.

        Args:
            provider_set: List of provider instances
            execution_order: Topologically sorted metric classes
            metric_configs: Config dict for metrics

        Returns:
            List of calculated metrics with tags merged
        """
        context, tags = self._execute_providers(provider_set)

        calculated: dict[type[Metric], Metric] = {}
        result_metrics: list[Metric] = []

        for metric_cls in execution_order:
            config = metric_configs.get(metric_cls.name, {})
            metric = metric_cls(**config)
            metric.tags.update(tags)
            metric.calculate(context, calculated)
            calculated[metric_cls] = metric
            result_metrics.append(metric)

        return result_metrics

    def measure(
        self,
        max_workers: int | None = None,
    ) -> MeasurementResult:
        """Execute the measurement pipeline.

        Args:
            max_workers: Max parallel workers. None = use all CPUs.

        Returns:
            MeasurementResult containing all calculated metrics and errors
        """
        import os
        from concurrent.futures import ProcessPoolExecutor, as_completed

        metric_configs: dict = {}
        if self._config_path:
            metric_configs = load_config(self._config_path)

        graph = build_dependency_graph(self._metrics)
        execution_order = topological_sort(graph)
        direct_metric_names = {m.name for m in self._metrics}

        # Collect required providers from metrics
        required_providers: set[type[Provider]] = set()
        for metric_cls in execution_order:
            required_providers.update(metric_cls.providers())

        # Use empty provider set if none specified and none required
        provider_sets = self._provider_sets if self._provider_sets else [[]]

        # Validate providers before running
        self._validate_providers(list(execution_order), provider_sets)

        all_metrics: list[Metric] = []
        all_errors: list[tuple[list[Provider], Exception]] = []
        workers = max_workers if max_workers is not None else os.cpu_count()

        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_provider_set = {
                executor.submit(
                    self._measure_single_provider_set,
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
                    all_errors.append((ps, e))

        return MeasurementResult(
            metrics=all_metrics,
            direct_metric_names=direct_metric_names,
            errors=all_errors,
        )
