"""
Metric calculation orchestration.
"""

import logging
from collections import defaultdict
from typing import Any

from checkup.errors import ProviderError
from checkup.executor.batch_executors import (
    execute_batch_asyncio,
    execute_batch_process,
    execute_batch_thread,
)
from checkup.executor.state import (
    CalculationState,
    create_failed_measurement,
    get_failed_dependencies,
    should_skip,
)
from checkup.measurement import Measurement, Measurements
from checkup.metric import ExecutorType, Metric
from checkup.provider import Provider

logger = logging.getLogger(__name__)

BATCH_EXECUTORS = {
    ExecutorType.THREAD: execute_batch_thread,
    ExecutorType.PROCESS: execute_batch_process,
    ExecutorType.ASYNCIO: execute_batch_asyncio,
}


class MetricCalculator:
    """
    Calculates metrics for a given context.
    """

    def calculate(
        self,
        metrics: list[Metric],
        execution_order: list[type[Metric]],
        context: dict[str, Any],
        tags: dict[str, Any],
        provided_classes: set[type[Provider]],
        failed_providers: dict[type[Provider], ProviderError] | None = None,
    ) -> list[Measurement]:
        """
        Calculate all metrics in execution order.
        """

        state = CalculationState(
            context=context,
            tags=tags,
            provided_classes=provided_classes,
            failed_providers=failed_providers or {},
            calculated=Measurements(),
        )
        class_to_instances = self._group_by_class(metrics, execution_order)

        i = 0
        while i < len(execution_order):
            i = self._process_at_index(execution_order, i, class_to_instances, state)

        logger.info(
            "Metric calculation complete: %d calculated, %d skipped, %d failed",
            len(state.results) - sum(len(state.calculated[c]) for c in state.failed),
            len(state.skipped),
            len(state.failed),
        )
        return state.results

    def _group_by_class(
        self,
        metrics: list[Metric],
        execution_order: list[type[Metric]],
    ) -> dict[type[Metric], list[Metric]]:
        """
        Group metric instances by class, creating defaults for dependencies.
        """

        grouped: dict[type[Metric], list[Metric]] = defaultdict(list)
        for m in metrics:
            grouped[type(m)].append(m)

        for metric_cls in execution_order:
            if metric_cls not in grouped:
                grouped[metric_cls].append(metric_cls())

        return grouped

    def _process_at_index(
        self,
        execution_order: list[type[Metric]],
        index: int,
        class_to_instances: dict[type[Metric], list[Metric]],
        state: CalculationState,
    ) -> int:
        """
        Process metric(s) at index, return next index to process.
        """

        metric_cls = execution_order[index]

        if should_skip(metric_cls, state.provided_classes, state.skipped):
            state.skipped.add(metric_cls)
            return index + 1

        failed_deps = get_failed_dependencies(
            metric_cls, state.failed_providers, state.failed
        )
        if failed_deps:
            self._record_failures(
                class_to_instances[metric_cls], metric_cls, failed_deps, state
            )
            return index + 1

        batch, next_index = self._build_batch(
            execution_order, index, class_to_instances, state
        )
        self._execute_batch(batch, metric_cls.get_executor(), state)
        return next_index

    def _build_batch(
        self,
        execution_order: list[type[Metric]],
        start: int,
        class_to_instances: dict[type[Metric], list[Metric]],
        state: CalculationState,
    ) -> tuple[list[Metric], int]:
        """
        Build a batch of metrics with the same executor type.
        """

        first_cls = execution_order[start]
        executor = first_cls.get_executor()
        batch: list[Metric] = list(class_to_instances[first_cls])
        batch_classes: set[type[Metric]] = {first_cls}
        i = start + 1

        while i < len(execution_order):
            cls = execution_order[i]

            if should_skip(cls, state.provided_classes, state.skipped):
                state.skipped.add(cls)
                i += 1
                continue

            failed_deps = get_failed_dependencies(
                cls, state.failed_providers, state.failed
            )
            if failed_deps:
                self._record_failures(class_to_instances[cls], cls, failed_deps, state)
                i += 1
                continue

            if cls.get_executor() != executor:
                break
            if set(cls.depends_on()) & batch_classes:
                break

            batch.extend(class_to_instances[cls])
            batch_classes.add(cls)
            i += 1

        return batch, i

    def _record_failures(
        self,
        instances: list[Metric],
        metric_cls: type[Metric],
        failed_deps: list[str],
        state: CalculationState,
    ) -> None:
        """
        Record failed measurements for metrics with failed dependencies.
        """

        for metric in instances:
            measurement = create_failed_measurement(metric, state.tags, failed_deps)
            state.calculated.append(metric_cls, measurement)
            state.results.append(measurement)
        state.failed.add(metric_cls)

    def _execute_batch(
        self,
        batch: list[Metric],
        executor_type: ExecutorType,
        state: CalculationState,
    ) -> None:
        """
        Execute a batch and record results.
        """

        logger.debug(
            "Executing batch with %d metrics using %s executor",
            len(batch),
            executor_type.value,
        )

        execute_fn = BATCH_EXECUTORS.get(executor_type)
        if not execute_fn:
            raise ValueError(f"Unknown executor type: {executor_type}")

        results = execute_fn(batch, state.context, state.tags, state.calculated)

        for metric, measurement in results:
            state.calculated.append(type(metric), measurement)
            state.results.append(measurement)
            logger.debug(
                "Metric %s calculated: value=%s", metric.name, measurement.value
            )
