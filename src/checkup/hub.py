"""CheckHub main orchestration."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Type

from pydantic import BaseModel, Field

from checkup.config import load_config
from checkup.graph import build_dependency_graph, topological_sort
from checkup.metric import Metric
from checkup.types import Context

if TYPE_CHECKING:
    from checkup.materializers import Materializer


class MeasurementResult(BaseModel):
    """Result of measuring metrics.

    Contains all calculated metrics and any errors from failed contexts.
    """

    metrics: list[Metric]
    errors: list[tuple[dict, Exception]] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    def materialize(self, materializer: "Materializer") -> None:
        """Output results using materializer.

        Args:
            materializer: Materializer instance for output
        """
        materializer.materialize(self.metrics)


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
        self._metrics: list[Type[Metric]] = []
        self._contexts: list[dict[str, Any]] = []
        self._config_path = config_path

    def with_metrics(self, metrics: Iterable[Type[Metric]]) -> "CheckHub":
        """Register metrics to calculate.

        Args:
            metrics: Iterable of metric classes

        Returns:
            Self for chaining
        """
        self._metrics.extend(metrics)
        return self

    def with_contexts(self, contexts: Iterable[dict[str, Any]]) -> "CheckHub":
        """Register contexts to calculate metrics for.

        Each context is a dict whose keys will be merged into metric tags.

        Args:
            contexts: Iterable of context dicts

        Returns:
            Self for chaining
        """
        self._contexts.extend(contexts)
        return self

    def _collect_providers(
        self,
        metrics: list[Type[Metric]],
    ) -> list[Callable[[Context], Context]]:
        """Collect and deduplicate providers from metrics.

        Args:
            metrics: List of metric classes

        Returns:
            List of unique provider functions (deduplicated by identity)
        """
        seen: set[int] = set()
        providers: list[Callable[[Context], Context]] = []

        for metric_cls in metrics:
            for provider in metric_cls.providers():
                provider_id = id(provider)
                if provider_id not in seen:
                    seen.add(provider_id)
                    providers.append(provider)

        return providers

    def _execute_providers(
        self,
        providers: list[Callable[[Context], Context]],
        initial_context: Context,
    ) -> Context:
        """Execute all providers and build enriched context.

        Args:
            providers: List of provider functions
            initial_context: Starting context

        Returns:
            Enriched context with all provider data
        """
        context = initial_context.copy()

        for provider in providers:
            context = provider(context)

        return context

    def _measure_single_context(
        self,
        context_dict: dict[str, Any],
        execution_order: list[Type[Metric]],
        providers: list[Callable[[Context], Context]],
        direct_metrics: set[Type[Metric]],
        metric_configs: dict,
    ) -> list[Metric]:
        """Calculate all metrics for a single context.

        Args:
            context_dict: Context dict to merge into metric tags
            execution_order: Topologically sorted metric classes
            providers: List of provider functions
            direct_metrics: Set of directly requested metric classes
            metric_configs: Config dict for metrics

        Returns:
            List of calculated metrics with context merged into tags
        """
        context: Context = context_dict.copy()
        context = self._execute_providers(providers, context)

        calculated: dict[Type[Metric], Metric] = {}
        result_metrics: list[Metric] = []

        for metric_cls in execution_order:
            config = metric_configs.get(metric_cls.name, {})
            metric = metric_cls(**config, is_direct=(metric_cls in direct_metrics))
            metric.tags.update(context_dict)
            metric.calculate(context, calculated)
            calculated[metric_cls] = metric
            result_metrics.append(metric)

        return result_metrics

    def measure(
        self,
        initial_context: Context | None = None,
        max_workers: int | None = None,
    ) -> MeasurementResult:
        """Execute the measurement pipeline.

        Args:
            initial_context: Optional starting context (used when no contexts registered)
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
        providers = self._collect_providers(list(execution_order))
        direct_metrics = set(self._metrics)

        if self._contexts:
            contexts = self._contexts
        else:
            contexts = [initial_context.copy() if initial_context else {}]

        all_metrics: list[Metric] = []
        all_errors: list[tuple[dict, Exception]] = []
        workers = max_workers if max_workers is not None else os.cpu_count()

        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_context = {
                executor.submit(
                    self._measure_single_context,
                    context_dict=ctx,
                    execution_order=execution_order,
                    providers=providers,
                    direct_metrics=direct_metrics,
                    metric_configs=metric_configs,
                ): ctx
                for ctx in contexts
            }

            for future in as_completed(future_to_context):
                ctx = future_to_context[future]
                try:
                    all_metrics.extend(future.result())
                except Exception as e:
                    all_errors.append((ctx, e))

        return MeasurementResult(metrics=all_metrics, errors=all_errors)
