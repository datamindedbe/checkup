"""CheckHub main orchestration."""

import asyncio
import inspect
import logging
import os
import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from pydantic import BaseModel, Field

from checkup.config import load_config
from checkup.graph import build_dependency_graph, topological_sort
from checkup.metric import ExecutorType, Metric
from checkup.provider import Provider
from checkup.types import Context

logger = logging.getLogger(__name__)


class MetricPicklingError(Exception):
    """Exception raised when a metric cannot be pickled for process execution."""

    def __init__(self, metric_cls: type[Metric], original_error: Exception):
        self.metric_cls = metric_cls
        self.original_error = original_error
        super().__init__(
            f"Metric '{metric_cls.name}' cannot be pickled for process execution. "
            f"Consider using ExecutorType.THREAD instead. Original error: {original_error}"
        )


def _validate_pickleable(metric_cls: type[Metric]) -> None:
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


class DuplicateMetricNameError(Exception):
    """Exception raised when multiple metrics have the same name."""

    def __init__(self, name: str, metric_classes: list[type[Metric]]):
        self.name = name
        self.metric_classes = metric_classes
        class_names = ", ".join(cls.__name__ for cls in metric_classes)
        super().__init__(
            f"Duplicate metric name '{name}' found in classes: {class_names}. "
            f"Each metric must have a unique name."
        )


def _validate_unique_metric_names(metrics: list[type[Metric]]) -> None:
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


if TYPE_CHECKING:
    from checkup.materializers import Materializer


def _calculate_metric_in_process(
    metric_cls: type[Metric],
    config: dict,
    context: Context,
    tags: dict[str, Any],
    calculated_data: dict[type[Metric], dict],
) -> Metric:
    """Calculate a single metric in a subprocess.

    This is a module-level function for ProcessPoolExecutor compatibility.

    Args:
        metric_cls: Metric class to instantiate and calculate
        config: Config dict for the metric
        context: Context dict from providers
        tags: Tags dict to merge into metrics
        calculated_data: Dict mapping metric classes to their serialized data

    Returns:
        Calculated metric instance
    """
    # Reconstruct calculated metrics from serialized data
    calculated: dict[type[Metric], Metric] = {}
    for cls, data in calculated_data.items():
        calculated[cls] = cls(**data)

    metric = metric_cls(**config)
    metric.tags.update(tags)
    metric.calculate(context, calculated)
    return metric


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


class ProviderError(Exception):
    """Exception raised when a provider fails during execution."""

    def __init__(self, provider: Provider, original_error: Exception):
        self.provider = provider
        self.original_error = original_error
        super().__init__(
            f"Provider '{provider.name}' failed: {original_error}"
        )


class ProviderExecutor:
    """Executes providers and builds context.

    Handles provider execution and separates tag data from regular context data.
    """

    def execute(
        self, provider_set: list[Provider], fail_fast: bool = True
    ) -> tuple[Context, dict[str, Any], list[ProviderError]]:
        """Execute all providers and build namespaced context.

        Each provider's data is added under its namespace (provider.name).
        Providers implementing is_tag_provider() have their data returned
        separately for merging into metric tags.

        Args:
            provider_set: List of provider instances
            fail_fast: If True, raise on first provider error.
                       If False, collect errors and continue.

        Returns:
            Tuple of (context dict, tags dict, list of errors)

        Raises:
            ProviderError: If fail_fast=True and a provider fails
        """
        context: Context = {}
        tags: dict[str, Any] = {}
        errors: list[ProviderError] = []

        for provider in provider_set:
            try:
                logger.debug("Executing provider: %s", provider.name)
                data = provider.provide()
                if provider.is_tag_provider():
                    tags.update(data)
                else:
                    context[provider.name] = data
                logger.debug("Provider %s completed successfully", provider.name)
            except Exception as e:
                error = ProviderError(provider, e)
                logger.error("Provider %s failed: %s", provider.name, e)
                if fail_fast:
                    raise error from e
                errors.append(error)

        return context, tags, errors


class MetricCalculator:
    """Calculates metrics for a given context."""

    def __init__(self, metric_configs: dict | None = None):
        """Initialize calculator with optional metric configs.

        Args:
            metric_configs: Optional dict mapping metric names to config dicts
        """
        self._configs = metric_configs or {}

    def calculate(
        self,
        execution_order: list[type[Metric]],
        context: Context,
        tags: dict[str, Any],
        provided_classes: set[type[Provider]],
    ) -> list[Metric]:
        """Calculate all metrics in execution order.

        Metrics are batched by executor type for efficient execution.
        Each batch is executed using the appropriate executor.

        Args:
            execution_order: Topologically sorted metric classes
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            provided_classes: Set of provider classes available

        Returns:
            List of calculated metrics
        """
        logger.debug(
            "Starting metric calculation for %d metrics", len(execution_order)
        )
        calculated: dict[type[Metric], Metric] = {}
        skipped: set[type[Metric]] = set()
        result_metrics: list[Metric] = []

        i = 0
        batch_num = 0
        while i < len(execution_order):
            metric_cls = execution_order[i]

            # Check for skip conditions
            if self._should_skip(metric_cls, provided_classes, skipped):
                skipped.add(metric_cls)
                i += 1
                continue

            # Start a new batch with this executor type
            current_executor = metric_cls.executor
            batch: list[type[Metric]] = [metric_cls]
            i += 1

            # Add more metrics to batch if they have same executor type
            # and don't depend on any metrics in the current batch
            batch_set = set(batch)
            while i < len(execution_order):
                next_cls = execution_order[i]

                if self._should_skip(next_cls, provided_classes, skipped):
                    skipped.add(next_cls)
                    i += 1
                    continue

                if next_cls.executor != current_executor:
                    break  # Different executor, start new batch

                # Check if this metric depends on any metric in the current batch
                if set(next_cls.depends_on()) & batch_set:
                    break  # Has dependency in batch, must process batch first

                batch.append(next_cls)
                batch_set.add(next_cls)
                i += 1

            # Execute the batch with appropriate executor
            batch_num += 1
            logger.debug(
                "Executing batch %d with %d metrics using %s executor",
                batch_num,
                len(batch),
                current_executor.value,
            )
            batch_results = self._execute_batch(
                batch, current_executor, context, tags, calculated
            )
            for metric_cls_result, metric in batch_results.items():
                calculated[metric_cls_result] = metric
                result_metrics.append(metric)
                logger.debug(
                    "Metric %s calculated: value=%s",
                    metric_cls_result.name,
                    metric.value,
                )

        logger.info(
            "Metric calculation complete: %d calculated, %d skipped",
            len(result_metrics),
            len(skipped),
        )
        return result_metrics

    def _should_skip(
        self,
        metric_cls: type[Metric],
        provided_classes: set[type[Provider]],
        skipped: set[type[Metric]],
    ) -> bool:
        """Check if a metric should be skipped.

        Args:
            metric_cls: Metric class to check
            provided_classes: Set of available provider classes
            skipped: Set of already skipped metric classes

        Returns:
            True if metric should be skipped
        """
        missing_providers = set(metric_cls.providers()) - provided_classes
        if missing_providers:
            logger.warning(
                "Skipping metric %s: missing providers %s",
                metric_cls.name,
                sorted(cls.name for cls in missing_providers),
            )
            return True

        skipped_deps = set(metric_cls.depends_on()) & skipped
        if skipped_deps:
            logger.warning(
                "Skipping metric %s: dependencies were skipped %s",
                metric_cls.name,
                sorted(cls.name for cls in skipped_deps),
            )
            return True

        return False

    def _execute_batch(
        self,
        batch: list[type[Metric]],
        executor_type: ExecutorType,
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Metric],
    ) -> dict[type[Metric], Metric]:
        """Execute a batch of metrics with the appropriate executor.

        Args:
            batch: List of metric classes to execute
            executor_type: Type of executor to use
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            calculated: Dict of already-calculated metrics

        Returns:
            Dict mapping metric classes to calculated metric instances
        """
        if executor_type == ExecutorType.THREAD:
            return self._execute_batch_thread(batch, context, tags, calculated)
        elif executor_type == ExecutorType.PROCESS:
            return self._execute_batch_process(batch, context, tags, calculated)
        elif executor_type == ExecutorType.ASYNCIO:
            return self._execute_batch_asyncio(batch, context, tags, calculated)
        else:
            raise ValueError(f"Unknown executor type: {executor_type}")

    def _execute_batch_thread(
        self,
        batch: list[type[Metric]],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Metric],
    ) -> dict[type[Metric], Metric]:
        """Execute metrics using ThreadPoolExecutor.

        Args:
            batch: List of metric classes to execute
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            calculated: Dict of already-calculated metrics

        Returns:
            Dict mapping metric classes to calculated metric instances
        """
        results: dict[type[Metric], Metric] = {}

        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            future_to_cls = {
                executor.submit(
                    self._calculate_single_metric,
                    metric_cls,
                    context,
                    tags,
                    calculated,
                ): metric_cls
                for metric_cls in batch
            }

            for future in as_completed(future_to_cls):
                metric_cls = future_to_cls[future]
                metric = future.result()
                results[metric_cls] = metric
                # Update calculated for subsequent metrics in the same batch
                calculated[metric_cls] = metric

        return results

    def _execute_batch_process(
        self,
        batch: list[type[Metric]],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Metric],
    ) -> dict[type[Metric], Metric]:
        """Execute metrics using ProcessPoolExecutor.

        Args:
            batch: List of metric classes to execute
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            calculated: Dict of already-calculated metrics

        Returns:
            Dict mapping metric classes to calculated metric instances

        Raises:
            MetricPicklingError: If a metric class cannot be pickled
        """
        # Validate all metrics in batch are pickleable before starting
        for metric_cls in batch:
            _validate_pickleable(metric_cls)

        results: dict[type[Metric], Metric] = {}

        with ProcessPoolExecutor(max_workers=len(batch)) as executor:
            future_to_cls = {
                executor.submit(
                    _calculate_metric_in_process,
                    metric_cls,
                    self._configs.get(metric_cls.name, {}),
                    context,
                    tags,
                    {cls: m.model_dump() for cls, m in calculated.items()},
                ): metric_cls
                for metric_cls in batch
            }

            for future in as_completed(future_to_cls):
                metric_cls = future_to_cls[future]
                try:
                    metric = future.result()
                    results[metric_cls] = metric
                    calculated[metric_cls] = metric
                except Exception as e:
                    logger.error(
                        "Metric %s failed in process executor: %s",
                        metric_cls.name,
                        e,
                    )
                    raise

        return results

    def _execute_batch_asyncio(
        self,
        batch: list[type[Metric]],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Metric],
    ) -> dict[type[Metric], Metric]:
        """Execute metrics using asyncio.

        Supports both sync and async calculate methods.

        Args:
            batch: List of metric classes to execute
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            calculated: Dict of already-calculated metrics

        Returns:
            Dict mapping metric classes to calculated metric instances
        """
        return asyncio.run(
            self._execute_batch_asyncio_impl(batch, context, tags, calculated)
        )

    async def _execute_batch_asyncio_impl(
        self,
        batch: list[type[Metric]],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Metric],
    ) -> dict[type[Metric], Metric]:
        """Async implementation of batch execution.

        Args:
            batch: List of metric classes to execute
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            calculated: Dict of already-calculated metrics

        Returns:
            Dict mapping metric classes to calculated metric instances
        """
        tasks = []
        for metric_cls in batch:
            metric = metric_cls(**self._configs.get(metric_cls.name, {}))
            metric.tags.update(tags)
            tasks.append(self._calculate_async_metric(metric, context, calculated))

        metrics = await asyncio.gather(*tasks)
        return {type(m): m for m in metrics}

    async def _calculate_async_metric(
        self,
        metric: Metric,
        context: Context,
        calculated: dict[type[Metric], Metric],
    ) -> Metric:
        """Calculate a single metric, handling both sync and async calculate methods.

        Args:
            metric: Metric instance to calculate
            context: Context dict from providers
            calculated: Dict of already-calculated metrics

        Returns:
            Calculated metric instance
        """
        if inspect.iscoroutinefunction(metric.calculate):
            await metric.calculate(context, calculated)
        else:
            metric.calculate(context, calculated)
        return metric

    def _calculate_single_metric(
        self,
        metric_cls: type[Metric],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Metric],
    ) -> Metric:
        """Calculate a single metric.

        Args:
            metric_cls: Metric class to instantiate and calculate
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            calculated: Dict of already-calculated metrics

        Returns:
            Calculated metric instance
        """
        metric = metric_cls(**self._configs.get(metric_cls.name, {}))
        metric.tags.update(tags)
        metric.calculate(context, calculated)
        return metric


def _collect_required_providers(metrics: list[type[Metric]]) -> set[type[Provider]]:
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


def _validate_providers(
    metrics: list[type[Metric]],
    provider_sets: list[list[Provider]],
) -> None:
    """Validate all required providers are present in each provider set.

    Logs a warning for any missing providers instead of failing.

    Args:
        metrics: List of metric classes to check
        provider_sets: List of provider instance lists to validate
    """
    required = _collect_required_providers(metrics)

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
    context, tags, errors = ProviderExecutor().execute(provider_set, fail_fast=True)
    # errors list will be empty if fail_fast=True since it raises on error
    return MetricCalculator(metric_configs).calculate(
        execution_order, context, tags, {type(p) for p in provider_set}
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
        _validate_unique_metric_names(list(execution_order))

        direct_metric_names = {m.name for m in self._metrics}

        # Use empty provider set if none specified and none required
        provider_sets = self._provider_sets if self._provider_sets else [[]]

        # Validate providers before running
        _validate_providers(list(execution_order), provider_sets)

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
                    logger.error(
                        "Provider set failed: %s",
                        e,
                        exc_info=True,
                    )
                    all_errors.append((ps, e))

        logger.info(
            "Measurement complete: %d metrics calculated, %d errors",
            len(all_metrics),
            len(all_errors),
        )
        return MeasurementResult(
            metrics=all_metrics,
            direct_metric_names=direct_metric_names,
            errors=all_errors,
        )
