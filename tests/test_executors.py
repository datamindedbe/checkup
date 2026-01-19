"""Tests for custom metric executors."""

from typing import ClassVar

from checkup.hub import CheckUp
from checkup.metric import ExecutorType, Metric
from checkup.types import Context


class ThreadMetric(Metric):
    """Metric that uses ThreadPoolExecutor (default)."""

    name: ClassVar[str] = "thread_metric"
    description: ClassVar[str] = "Thread-based metric"
    unit: ClassVar[str] = "count"
    # executor defaults to ExecutorType.THREAD

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 10
        self.diagnostic = "Calculated in thread"


class ProcessMetric(Metric):
    """Metric that uses ProcessPoolExecutor."""

    name: ClassVar[str] = "process_metric"
    description: ClassVar[str] = "Process-based metric"
    unit: ClassVar[str] = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.PROCESS

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 20
        self.diagnostic = "Calculated in process"


class AsyncMetric(Metric):
    """Metric that uses asyncio executor."""

    name: ClassVar[str] = "async_metric"
    description: ClassVar[str] = "Async metric"
    unit: ClassVar[str] = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 30
        self.diagnostic = "Calculated with asyncio"


class AsyncMetricWithAsyncCalculate(Metric):
    """Metric that uses asyncio executor with async calculate method."""

    name: ClassVar[str] = "async_metric_native"
    description: ClassVar[str] = "Native async metric"
    unit: ClassVar[str] = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO

    async def calculate(self, context: Context, metrics: dict) -> None:
        import asyncio

        await asyncio.sleep(0.001)  # Small async operation
        self.value = 40
        self.diagnostic = "Calculated with native async"


class DependentThreadMetric(Metric):
    """Thread metric that depends on another thread metric."""

    name: ClassVar[str] = "dependent_thread"
    description: ClassVar[str] = "Depends on thread metric"
    unit: ClassVar[str] = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.THREAD

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [ThreadMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        base_value = metrics[ThreadMetric].value
        self.value = base_value * 2
        self.diagnostic = f"Doubled thread metric: {base_value} -> {self.value}"


class DependentProcessMetric(Metric):
    """Process metric that depends on a thread metric."""

    name: ClassVar[str] = "dependent_process"
    description: ClassVar[str] = "Process metric depending on thread metric"
    unit: ClassVar[str] = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.PROCESS

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [ThreadMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        base_value = metrics[ThreadMetric].value
        self.value = base_value * 3
        self.diagnostic = f"Tripled thread metric: {base_value} -> {self.value}"


class DependentAsyncMetric(Metric):
    """Async metric that depends on a process metric."""

    name: ClassVar[str] = "dependent_async"
    description: ClassVar[str] = "Async metric depending on process metric"
    unit: ClassVar[str] = "count"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [ProcessMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        base_value = metrics[ProcessMetric].value
        self.value = base_value + 5
        self.diagnostic = f"Added 5 to process metric: {base_value} -> {self.value}"


def test_default_executor_is_thread():
    """Test that the default executor is ThreadPoolExecutor."""
    assert ThreadMetric.executor == ExecutorType.THREAD


def test_process_executor_specified():
    """Test that ProcessPoolExecutor can be specified."""
    assert ProcessMetric.executor == ExecutorType.PROCESS


def test_asyncio_executor_specified():
    """Test that asyncio executor can be specified."""
    assert AsyncMetric.executor == ExecutorType.ASYNCIO


def test_thread_metric_calculation():
    """Test calculating a metric with ThreadPoolExecutor."""
    result = CheckUp().with_metrics([ThreadMetric]).measure()

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "thread_metric"
    assert result.metrics[0].value == 10


def test_process_metric_calculation():
    """Test calculating a metric with ProcessPoolExecutor."""
    result = CheckUp().with_metrics([ProcessMetric]).measure()

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "process_metric"
    assert result.metrics[0].value == 20


def test_asyncio_metric_calculation():
    """Test calculating a metric with asyncio executor."""
    result = CheckUp().with_metrics([AsyncMetric]).measure()

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "async_metric"
    assert result.metrics[0].value == 30


def test_asyncio_metric_with_async_calculate():
    """Test calculating a metric with native async calculate method."""
    result = CheckUp().with_metrics([AsyncMetricWithAsyncCalculate]).measure()

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "async_metric_native"
    assert result.metrics[0].value == 40


def test_mixed_executor_types():
    """Test calculating metrics with different executor types."""
    result = CheckUp().with_metrics(
        [ThreadMetric, ProcessMetric, AsyncMetric]
    ).measure()

    assert len(result.metrics) == 3
    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["thread_metric"].value == 10
    assert metrics_by_name["process_metric"].value == 20
    assert metrics_by_name["async_metric"].value == 30


def test_thread_dependency_chain():
    """Test dependency chain within thread executor."""
    result = CheckUp().with_metrics([DependentThreadMetric]).measure()

    assert len(result.metrics) == 2
    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["thread_metric"].value == 10
    assert metrics_by_name["dependent_thread"].value == 20


def test_cross_executor_dependencies():
    """Test dependencies across different executor types."""
    result = CheckUp().with_metrics([DependentProcessMetric]).measure()

    assert len(result.metrics) == 2
    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["thread_metric"].value == 10
    assert metrics_by_name["dependent_process"].value == 30


def test_async_depends_on_process():
    """Test async metric depending on process metric."""
    result = CheckUp().with_metrics([DependentAsyncMetric]).measure()

    assert len(result.metrics) == 2
    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["process_metric"].value == 20
    assert metrics_by_name["dependent_async"].value == 25


def test_complex_mixed_dependencies():
    """Test complex dependency graph with mixed executor types."""
    result = CheckUp().with_metrics(
        [DependentThreadMetric, DependentProcessMetric, DependentAsyncMetric]
    ).measure()

    # ThreadMetric -> DependentThreadMetric (thread -> thread)
    # ThreadMetric -> DependentProcessMetric (thread -> process)
    # ProcessMetric -> DependentAsyncMetric (process -> async)
    assert len(result.metrics) == 5

    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["thread_metric"].value == 10
    assert metrics_by_name["dependent_thread"].value == 20
    assert metrics_by_name["dependent_process"].value == 30
    assert metrics_by_name["process_metric"].value == 20
    assert metrics_by_name["dependent_async"].value == 25
