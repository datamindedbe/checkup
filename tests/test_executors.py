"""Tests for custom metric executors."""

from typing import ClassVar

from checkup.hub import CheckHub
from checkup.metric import ExecutorType, Measurement, Metric
from checkup.types import Context


class ThreadMetric(Metric):
    """Metric that uses ThreadPoolExecutor (default)."""

    name: str = "thread_metric"
    description: str = "Thread-based metric"
    unit: str = "count"
    # executor defaults to ExecutorType.THREAD

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        return self.measure(value=10, diagnostic="Calculated in thread")


class ProcessMetric(Metric):
    """Metric that uses ProcessPoolExecutor."""

    name: str = "process_metric"
    description: str = "Process-based metric"
    unit: str = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.PROCESS

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        return self.measure(value=20, diagnostic="Calculated in process")


class AsyncMetric(Metric):
    """Metric that uses asyncio executor."""

    name: str = "async_metric"
    description: str = "Async metric"
    unit: str = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        return self.measure(value=30, diagnostic="Calculated with asyncio")


class AsyncMetricWithAsyncCalculate(Metric):
    """Metric that uses asyncio executor with async calculate method."""

    name: str = "async_metric_native"
    description: str = "Native async metric"
    unit: str = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO

    async def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        import asyncio

        await asyncio.sleep(0.001)  # Small async operation
        return self.measure(value=40, diagnostic="Calculated with native async")


class DependentThreadMetric(Metric):
    """Thread metric that depends on another thread metric."""

    name: str = "dependent_thread"
    description: str = "Depends on thread metric"
    unit: str = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.THREAD

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [ThreadMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        base_value = self.get_single(measurements, ThreadMetric).value
        value = base_value * 2
        return self.measure(
            value=value, diagnostic=f"Doubled thread metric: {base_value} -> {value}"
        )


class DependentProcessMetric(Metric):
    """Process metric that depends on a thread metric."""

    name: str = "dependent_process"
    description: str = "Process metric depending on thread metric"
    unit: str = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.PROCESS

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [ThreadMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        base_value = self.get_single(measurements, ThreadMetric).value
        value = base_value * 3
        return self.measure(
            value=value, diagnostic=f"Tripled thread metric: {base_value} -> {value}"
        )


class DependentAsyncMetric(Metric):
    """Async metric that depends on a process metric."""

    name: str = "dependent_async"
    description: str = "Async metric depending on process metric"
    unit: str = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [ProcessMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        base_value = self.get_single(measurements, ProcessMetric).value
        value = base_value + 5
        return self.measure(
            value=value,
            diagnostic=f"Added 5 to process metric: {base_value} -> {value}",
        )


def test_default_executor_is_thread():
    """Test that the default executor is ThreadPoolExecutor."""
    assert ThreadMetric().get_executor() == ExecutorType.THREAD


def test_process_executor_specified():
    """Test that ProcessPoolExecutor can be specified."""
    assert ProcessMetric().get_executor() == ExecutorType.PROCESS


def test_asyncio_executor_specified():
    """Test that asyncio executor can be specified."""
    assert AsyncMetric().get_executor() == ExecutorType.ASYNCIO


def test_thread_metric_calculation():
    """Test calculating a metric with ThreadPoolExecutor."""
    result = CheckHub().with_metrics([ThreadMetric()]).measure()

    assert len(result.measurements) == 1
    assert result.measurements[0].metric.name == "thread_metric"
    assert result.measurements[0].value == 10


def test_process_metric_calculation():
    """Test calculating a metric with ProcessPoolExecutor."""
    result = CheckHub().with_metrics([ProcessMetric()]).measure()

    assert len(result.measurements) == 1
    assert result.measurements[0].metric.name == "process_metric"
    assert result.measurements[0].value == 20


def test_asyncio_metric_calculation():
    """Test calculating a metric with asyncio executor."""
    result = CheckHub().with_metrics([AsyncMetric()]).measure()

    assert len(result.measurements) == 1
    assert result.measurements[0].metric.name == "async_metric"
    assert result.measurements[0].value == 30


def test_asyncio_metric_with_async_calculate():
    """Test calculating a metric with native async calculate method."""
    result = CheckHub().with_metrics([AsyncMetricWithAsyncCalculate()]).measure()

    assert len(result.measurements) == 1
    assert result.measurements[0].metric.name == "async_metric_native"
    assert result.measurements[0].value == 40


def test_mixed_executor_types():
    """Test calculating metrics with different executor types."""
    result = (
        CheckHub()
        .with_metrics([ThreadMetric(), ProcessMetric(), AsyncMetric()])
        .measure()
    )

    assert len(result.measurements) == 3
    measurements_by_name = {m.metric.name: m for m in result.measurements}
    assert measurements_by_name["thread_metric"].value == 10
    assert measurements_by_name["process_metric"].value == 20
    assert measurements_by_name["async_metric"].value == 30


def test_thread_dependency_chain():
    """Test dependency chain within thread executor."""
    result = (
        CheckHub().with_metrics([DependentThreadMetric(), ThreadMetric()]).measure()
    )

    assert len(result.measurements) == 2
    measurements_by_name = {m.metric.name: m for m in result.measurements}
    assert measurements_by_name["thread_metric"].value == 10
    assert measurements_by_name["dependent_thread"].value == 20


def test_cross_executor_dependencies():
    """Test dependencies across different executor types."""
    result = (
        CheckHub().with_metrics([DependentProcessMetric(), ThreadMetric()]).measure()
    )

    assert len(result.measurements) == 2
    measurements_by_name = {m.metric.name: m for m in result.measurements}
    assert measurements_by_name["thread_metric"].value == 10
    assert measurements_by_name["dependent_process"].value == 30


def test_async_depends_on_process():
    """Test async metric depending on process metric."""
    result = (
        CheckHub().with_metrics([DependentAsyncMetric(), ProcessMetric()]).measure()
    )

    assert len(result.measurements) == 2
    measurements_by_name = {m.metric.name: m for m in result.measurements}
    assert measurements_by_name["process_metric"].value == 20
    assert measurements_by_name["dependent_async"].value == 25


def test_complex_mixed_dependencies():
    """Test complex dependency graph with mixed executor types."""
    result = (
        CheckHub()
        .with_metrics(
            [
                DependentThreadMetric(),
                DependentProcessMetric(),
                DependentAsyncMetric(),
            ]
        )
        .measure()
    )

    # ThreadMetric -> DependentThreadMetric (thread -> thread)
    # ThreadMetric -> DependentProcessMetric (thread -> process)
    # ProcessMetric -> DependentAsyncMetric (process -> async)
    assert len(result.measurements) == 5

    measurements_by_name = {m.metric.name: m for m in result.measurements}
    assert measurements_by_name["thread_metric"].value == 10
    assert measurements_by_name["dependent_thread"].value == 20
    assert measurements_by_name["dependent_process"].value == 30
    assert measurements_by_name["process_metric"].value == 20
    assert measurements_by_name["dependent_async"].value == 25
