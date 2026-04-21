"""Executor classes for provider and metric execution."""

import asyncio
import inspect
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any

from checkup.errors import ProviderError
from checkup.metric import ExecutorType, Measurement, Metric
from checkup.provider import Provider
from checkup.types import Context
from checkup.validators import validate_pickleable

logger = logging.getLogger(__name__)


def _calculate_metric_in_process(
    metric: Metric,
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], Measurement],
) -> Measurement:
    """Calculate a single metric in a subprocess.

    This is a module-level function for ProcessPoolExecutor compatibility.

    Args:
        metric: Metric instance to calculate
        context: Context dict from providers
        tags: Tags dict to merge into metrics
        calculated: Dict mapping metric classes to Measurements

    Returns:
        Calculated Measurement
    """

    measurement = metric.calculate(context, calculated)
    measurement.tags.update(tags)
    return measurement


class ProviderExecutor:
    """Executes providers and builds context.

    Handles provider execution and separates tag data from regular context data.
    """

    def execute(
        self, provider_set: list[Provider]
    ) -> tuple[Context, dict[str, Any], list[ProviderError]]:
        """Execute all providers and build namespaced context.

        Each provider's data is added under its namespace (provider.name).
        Providers implementing is_tag_provider() have their data returned
        separately for merging into metric tags.

        Args:
            provider_set: List of provider instances

        Returns:
            Tuple of (context dict, tags dict, list of errors)
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
                errors.append(error)

        return context, tags, errors


class MetricCalculator:
    """Calculates metrics for a given context."""

    def calculate(
        self,
        metrics: list[Metric],
        execution_order: list[type[Metric]],
        context: Context,
        tags: dict[str, Any],
        provided_classes: set[type[Provider]],
        failed_providers: dict[type[Provider], ProviderError] | None = None,
    ) -> list[Measurement]:
        """Calculate all metrics in execution order.

        Metrics are batched by executor type for efficient execution.
        Each batch is executed using the appropriate executor.

        Args:
            metrics: List of metric instances to calculate
            execution_order: Topologically sorted metric classes
            context: Context dict from providers
            tags: Tags dict to merge into metrics
            provided_classes: Set of provider classes available
            failed_providers: Dict mapping failed provider classes to their errors

        Returns:
            List of Measurements
        """
        failed_providers = failed_providers or {}
        logger.debug("Starting metric calculation for %d metrics", len(execution_order))

        class_to_instance: dict[type[Metric], Metric] = {type(m): m for m in metrics}

        for metric_cls in execution_order:
            if metric_cls not in class_to_instance:
                # Instantiate dependent metrics implicitly with default constructor.
                class_to_instance[metric_cls] = metric_cls()

        calculated: dict[type[Metric], Measurement] = {}
        skipped: set[type[Metric]] = set()
        failed: set[type[Metric]] = set()
        result_measurements: list[Measurement] = []

        i = 0
        batch_num = 0
        while i < len(execution_order):
            metric_cls = execution_order[i]

            # Check for skip conditions (missing providers)
            if self._should_skip(metric_cls, provided_classes, skipped):
                skipped.add(metric_cls)
                i += 1
                continue

            metric = class_to_instance[metric_cls]

            # Check for failed provider dependencies
            failed_deps = self._get_failed_providers(
                metric_cls, failed_providers, failed
            )
            if failed_deps:
                measurement = self._create_failed_measurement(metric, tags, failed_deps)
                calculated[metric_cls] = measurement
                result_measurements.append(measurement)
                failed.add(metric_cls)
                i += 1
                continue

            # Start a new batch with this executor type
            current_executor = metric_cls.executor
            batch: list[Metric] = [metric]
            i += 1

            # Add more metrics to batch if they have same executor type
            # and don't depend on any metrics in the current batch
            batch_classes = {metric_cls}
            while i < len(execution_order):
                next_cls = execution_order[i]

                if self._should_skip(next_cls, provided_classes, skipped):
                    skipped.add(next_cls)
                    i += 1
                    continue

                next_metric = class_to_instance[next_cls]

                failed_deps = self._get_failed_providers(
                    next_cls, failed_providers, failed
                )
                if failed_deps:
                    measurement = self._create_failed_measurement(
                        next_metric, tags, failed_deps
                    )
                    calculated[next_cls] = measurement
                    result_measurements.append(measurement)
                    failed.add(next_cls)
                    i += 1
                    continue

                if next_cls.executor != current_executor:
                    break  # Different executor, start new batch

                # Check if this metric depends on any metric in the current batch
                if set(next_cls.depends_on()) & batch_classes:
                    break  # Has dependency in batch, must process batch first

                batch.append(next_metric)
                batch_classes.add(next_cls)
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
            for metric_cls_key, measurement in batch_results.items():
                calculated[metric_cls_key] = measurement
                result_measurements.append(measurement)
                logger.debug(
                    "Metric %s calculated: value=%s",
                    metric_cls_key.name,
                    measurement.value,
                )

        logger.info(
            "Metric calculation complete: %d calculated, %d skipped, %d failed",
            len(result_measurements) - len(failed),
            len(skipped),
            len(failed),
        )
        return result_measurements

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
            logger.debug(
                "Skipping metric %s: missing providers %s",
                metric_cls.name,
                sorted(cls.name for cls in missing_providers),
            )
            return True

        skipped_deps = set(metric_cls.depends_on()) & skipped
        if skipped_deps:
            logger.debug(
                "Skipping metric %s: dependencies were skipped %s",
                metric_cls.name,
                sorted(cls.name for cls in skipped_deps),
            )
            return True

        return False

    def _get_failed_providers(
        self,
        metric_cls: type[Metric],
        failed_providers: dict[type[Provider], ProviderError],
        failed_metrics: set[type[Metric]],
    ) -> list[str]:
        """Get list of failed provider/metric names that this metric depends on.

        Args:
            metric_cls: Metric class to check
            failed_providers: Dict of failed provider classes to errors
            failed_metrics: Set of metrics that failed due to provider errors

        Returns:
            List of failed provider/metric names, empty if none
        """
        failed_names = []

        # Check direct provider dependencies
        for provider_cls in metric_cls.providers():
            if provider_cls in failed_providers:
                failed_names.append(f"provider '{provider_cls.name}'")

        # Check metric dependencies that failed
        for dep_cls in metric_cls.depends_on():
            if dep_cls in failed_metrics:
                failed_names.append(f"metric '{dep_cls.name}'")

        return failed_names

    def _create_failed_measurement(
        self,
        metric: Metric,
        tags: dict[str, Any],
        failed_deps: list[str],
    ) -> Measurement:
        """Create a Measurement with null value due to failed dependencies.

        Args:
            metric: Metric instance
            tags: Tags to merge into the measurement
            failed_deps: List of failed dependency names

        Returns:
            Measurement with value=None and diagnostic explaining failure
        """
        diagnostic = f"Failed: {', '.join(failed_deps)} failed"
        logger.debug(
            "Metric %s marked as failed: %s",
            metric.name,
            diagnostic,
        )
        return Measurement(
            metric=metric,
            value=None,
            tags=dict(tags),
            diagnostic=diagnostic,
        )

    def _execute_batch(
        self,
        batch: list[Metric],
        executor_type: ExecutorType,
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> dict[type[Metric], Measurement]:
        """Execute a batch of metrics with the appropriate executor.

        Args:
            batch: List of metric instances to execute
            executor_type: Type of executor to use
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Dict mapping metric classes to Measurements
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
        batch: list[Metric],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> dict[type[Metric], Measurement]:
        """Execute metrics using ThreadPoolExecutor.

        Args:
            batch: List of metric instances to execute
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Dict mapping metric classes to Measurements
        """
        results: dict[type[Metric], Measurement] = {}

        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            future_to_metric = {
                executor.submit(
                    self._calculate_single_metric,
                    metric,
                    context,
                    tags,
                    calculated,
                ): metric
                for metric in batch
            }

            for future in as_completed(future_to_metric):
                metric = future_to_metric[future]
                measurement = future.result()
                results[type(metric)] = measurement
                calculated[type(metric)] = measurement

        return results

    def _execute_batch_process(
        self,
        batch: list[Metric],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> dict[type[Metric], Measurement]:
        """Execute metrics using ProcessPoolExecutor.

        Args:
            batch: List of metric instances to execute
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Dict mapping metric classes to Measurements

        Raises:
            MetricPicklingError: If a metric cannot be pickled
        """

        for metric in batch:
            validate_pickleable(type(metric))

        results: dict[type[Metric], Measurement] = {}

        with ProcessPoolExecutor(max_workers=len(batch)) as executor:
            future_to_metric = {
                executor.submit(
                    _calculate_metric_in_process,
                    metric,
                    context,
                    tags,
                    calculated,
                ): metric
                for metric in batch
            }

            for future in as_completed(future_to_metric):
                metric = future_to_metric[future]
                try:
                    measurement = future.result()
                    results[type(metric)] = measurement
                    calculated[type(metric)] = measurement
                except Exception as e:
                    logger.error(
                        "Metric %s failed in process executor: %s",
                        metric.name,
                        e,
                    )
                    raise

        return results

    def _execute_batch_asyncio(
        self,
        batch: list[Metric],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> dict[type[Metric], Measurement]:
        """Execute metrics using asyncio.

        Supports both sync and async calculate methods.

        Args:
            batch: List of metric instances to execute
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Dict mapping metric classes to Measurements
        """
        return asyncio.run(
            self._execute_batch_asyncio_impl(batch, context, tags, calculated)
        )

    async def _execute_batch_asyncio_impl(
        self,
        batch: list[Metric],
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> dict[type[Metric], Measurement]:
        """Async implementation of batch execution.

        Args:
            batch: List of metric instances to execute
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Dict mapping metric classes to Measurements
        """
        tasks = [
            self._calculate_async_metric(metric, context, tags, calculated)
            for metric in batch
        ]
        results = await asyncio.gather(*tasks)
        return {type(m): r for m, r in zip(batch, results, strict=True)}

    async def _calculate_async_metric(
        self,
        metric: Metric,
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> Measurement:
        """Calculate a single metric, handling both sync and async calculate methods.

        Args:
            metric: Metric instance to calculate
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Measurement
        """
        if inspect.iscoroutinefunction(metric.calculate):
            measurement = await metric.calculate(context, calculated)
        else:
            measurement = metric.calculate(context, calculated)
        measurement.tags.update(tags)
        return measurement

    def _calculate_single_metric(
        self,
        metric: Metric,
        context: Context,
        tags: dict[str, Any],
        calculated: dict[type[Metric], Measurement],
    ) -> Measurement:
        """Calculate a single metric.

        Args:
            metric: Metric instance to calculate
            context: Context dict from providers
            tags: Tags dict to merge into measurements
            calculated: Dict of already-calculated measurements (keyed by class)

        Returns:
            Measurement
        """
        measurement = metric.calculate(context, calculated)
        measurement.tags.update(tags)
        return measurement
