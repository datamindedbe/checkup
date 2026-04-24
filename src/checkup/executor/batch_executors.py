"""Batch execution strategies for different executor types."""

import asyncio
import inspect
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup.validators import validate_pickleable

logger = logging.getLogger(__name__)


def _calculate_metric_in_process(
    metric: Metric,
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> Measurement:
    """
    Calculate a single metric in a subprocess.

    Module-level function for ProcessPoolExecutor compatibility.
    """

    measurement = metric.calculate(context, calculated)
    measurement.tags.update(tags)
    return measurement


def execute_batch_thread(
    batch: list[Metric],
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> list[tuple[Metric, Measurement]]:
    """
    Execute metrics using ThreadPoolExecutor.
    """

    results: list[tuple[Metric, Measurement]] = []

    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
        future_to_metric = {
            executor.submit(
                _calculate_single_metric,
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
            results.append((metric, measurement))

    return results


def execute_batch_process(
    batch: list[Metric],
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> list[tuple[Metric, Measurement]]:
    """
    Execute metrics using ProcessPoolExecutor.
    """

    for metric in batch:
        validate_pickleable(type(metric))

    results: list[tuple[Metric, Measurement]] = []

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
                results.append((metric, measurement))
            except Exception as e:
                logger.error(
                    "Metric %s failed in process executor: %s",
                    metric.name,
                    e,
                )
                raise

    return results


def execute_batch_asyncio(
    batch: list[Metric],
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> list[tuple[Metric, Measurement]]:
    """
    Execute metrics using asyncio.
    """

    return asyncio.run(_execute_batch_asyncio_impl(batch, context, tags, calculated))


async def _execute_batch_asyncio_impl(
    batch: list[Metric],
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> list[tuple[Metric, Measurement]]:
    """
    Async implementation of batch execution.
    """

    tasks = [
        _calculate_async_metric(metric, context, tags, calculated) for metric in batch
    ]
    measurements = await asyncio.gather(*tasks)
    return list(zip(batch, measurements, strict=True))


async def _calculate_async_metric(
    metric: Metric,
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> Measurement:
    """
    Calculate a single metric, handling both sync and async calculate methods.
    """

    if inspect.iscoroutinefunction(metric.calculate):
        measurement = await metric.calculate(context, calculated)
    else:
        measurement = metric.calculate(context, calculated)
    measurement.tags.update(tags)
    return measurement


def _calculate_single_metric(
    metric: Metric,
    context: Context,
    tags: dict[str, Any],
    calculated: dict[type[Metric], list[Measurement]],
) -> Measurement:
    """
    Calculate a single metric (for thread executor).
    """

    measurement = metric.calculate(context, calculated)
    measurement.tags.update(tags)
    return measurement
