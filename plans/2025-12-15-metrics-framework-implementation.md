# Metrics Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an extensible metrics calculation framework with dependency resolution, context providers, and multiple output formats.

**Architecture:** ABC-based plugin system with Pydantic models. Two-phase execution: providers enrich context, then metrics calculate in topological order with caching. Metrics are instances configured via YAML bounds.

**Tech Stack:** Python 3.12, Pydantic, pytest

---

## Task 1: Setup Project Structure

**Files:**
- Create: `src/checkup/types.py`
- Create: `tests/conftest.py`
- Modify: `pyproject.toml`

**Step 1: Add test dependencies to pyproject.toml**

Edit the file to add:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]
```

**Step 2: Install test dependencies**

Run: `uv pip install -e ".[dev]"`
Expected: Dependencies installed successfully

**Step 3: Create type aliases file**

Create `src/checkup/types.py`:

```python
"""Type aliases for the checkup framework."""
from typing import Any

Context = dict[str, Any]
```

**Step 4: Create pytest configuration**

Create `tests/conftest.py`:

```python
"""Pytest configuration and shared fixtures."""
import pytest
```

**Step 5: Verify test setup**

Run: `pytest tests/ -v`
Expected: "no tests ran" (but pytest works)

**Step 6: Commit**

```bash
git add pyproject.toml src/checkup/types.py tests/conftest.py
git commit -m "chore: setup test infrastructure"
```

---

## Task 2: Metric ABC and DummyMetric

**Files:**
- Modify: `src/checkup/metric.py`
- Create: `tests/test_metric.py`

**Step 1: Write failing test for DummyMetric instantiation**

Create `tests/test_metric.py`:

```python
"""Tests for Metric ABC and test fixtures."""
from checkup.metric import DummyMetric
from checkup.types import Context


def test_dummy_metric_instantiation():
    """Test that DummyMetric can be instantiated with config."""
    metric = DummyMetric(expected_value=42)

    assert metric.name == "dummy"
    assert metric.description == "Test metric"
    assert metric.unit == "count"
    assert metric.value is None
    assert metric.expected_value == 42
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_metric.py::test_dummy_metric_instantiation -v`
Expected: FAIL with import error or class not found

**Step 3: Implement Metric ABC**

Modify `src/checkup/metric.py`:

```python
"""Metric base class and test fixtures."""
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

from checkup.types import Context


class Metric(ABC, BaseModel):
    """Base class for all metrics.

    Metrics are Pydantic models that calculate values from context.
    They can depend on other metrics and declare providers for context enrichment.
    """

    # Core attributes
    name: str
    description: str
    unit: str
    tags: dict = Field(default_factory=dict)

    # Calculated value (set by calculate())
    value: Any = None

    @abstractmethod
    def calculate(self, context: Context, metrics: dict[type['Metric'], 'Metric']) -> None:
        """Calculate metric value and set self.value.

        Args:
            context: General context enriched by providers
            metrics: Dict of already-calculated metric instances (dependencies)
        """
        pass

    @classmethod
    def depends_on(cls) -> list[type['Metric']]:
        """Return list of metric classes this metric depends on.

        Returns:
            List of metric classes (empty by default)
        """
        return []

    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        """Return list of provider functions to enrich context.

        Returns:
            List of provider functions (empty by default)
        """
        return []


class DummyMetric(Metric):
    """Simple test metric with no dependencies.

    Always returns the expected_value from config.
    Used for testing the framework.
    """

    name: str = "dummy"
    description: str = "Test metric"
    unit: str = "count"

    expected_value: int = 42

    def calculate(self, context: Context, metrics: dict) -> None:
        """Set value to expected_value."""
        self.value = self.expected_value
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_metric.py::test_dummy_metric_instantiation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/checkup/metric.py tests/test_metric.py
git commit -m "feat: add Metric ABC and DummyMetric"
```

---

## Task 3: DummyMetric Calculation

**Files:**
- Modify: `tests/test_metric.py`

**Step 1: Write failing test for DummyMetric calculation**

Add to `tests/test_metric.py`:

```python
def test_dummy_metric_calculate():
    """Test that DummyMetric.calculate() sets value correctly."""
    metric = DummyMetric(expected_value=100)

    assert metric.value is None

    metric.calculate(context={}, metrics={})

    assert metric.value == 100
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_metric.py::test_dummy_metric_calculate -v`
Expected: PASS (implementation already exists)

**Step 3: Commit**

```bash
git add tests/test_metric.py
git commit -m "test: add DummyMetric calculation test"
```

---

## Task 4: DependentDummyMetric

**Files:**
- Modify: `src/checkup/metric.py`
- Modify: `tests/test_metric.py`

**Step 1: Write failing test for dependent metric**

Add to `tests/test_metric.py`:

```python
def test_dependent_metric_depends_on():
    """Test that DependentDummyMetric declares dependencies."""
    from checkup.metric import DependentDummyMetric

    deps = DependentDummyMetric.depends_on()

    assert deps == [DummyMetric]


def test_dependent_metric_calculate():
    """Test that DependentDummyMetric uses dependency value."""
    from checkup.metric import DependentDummyMetric

    # Calculate dependency first
    base_metric = DummyMetric(expected_value=10)
    base_metric.calculate(context={}, metrics={})

    # Calculate dependent metric
    dependent = DependentDummyMetric()
    dependent.calculate(
        context={},
        metrics={DummyMetric: base_metric}
    )

    assert dependent.value == 20  # 10 * 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_metric.py::test_dependent_metric_depends_on -v`
Expected: FAIL with import error

**Step 3: Implement DependentDummyMetric**

Add to `src/checkup/metric.py`:

```python
class DependentDummyMetric(Metric):
    """Test metric that depends on DummyMetric.

    Doubles the value of DummyMetric.
    Used for testing dependency resolution.
    """

    name: str = "dependent_dummy"
    description: str = "Depends on DummyMetric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type['Metric']]:
        """Depends on DummyMetric."""
        return [DummyMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        """Double the DummyMetric value."""
        base_value = metrics[DummyMetric].value
        self.value = base_value * 2
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_metric.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/checkup/metric.py tests/test_metric.py
git commit -m "feat: add DependentDummyMetric for testing dependencies"
```

---

## Task 5: Dependency Graph Building

**Files:**
- Create: `src/checkup/graph.py`
- Create: `tests/test_graph.py`

**Step 1: Write failing test for dependency graph building**

Create `tests/test_graph.py`:

```python
"""Tests for dependency graph construction and topological sorting."""
from checkup.graph import build_dependency_graph
from checkup.metric import DummyMetric, DependentDummyMetric


def test_build_dependency_graph_no_deps():
    """Test building graph for metric with no dependencies."""
    graph = build_dependency_graph([DummyMetric])

    assert graph == {DummyMetric: []}


def test_build_dependency_graph_with_deps():
    """Test building graph for metrics with dependencies."""
    graph = build_dependency_graph([DependentDummyMetric, DummyMetric])

    assert graph == {
        DummyMetric: [],
        DependentDummyMetric: [DummyMetric]
    }
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph.py::test_build_dependency_graph_no_deps -v`
Expected: FAIL with import error

**Step 3: Implement build_dependency_graph**

Create `src/checkup/graph.py`:

```python
"""Dependency graph construction and topological sorting."""
from typing import Type

from checkup.metric import Metric


def build_dependency_graph(
    metrics: list[Type[Metric]]
) -> dict[Type[Metric], list[Type[Metric]]]:
    """Build dependency graph from metric classes.

    Args:
        metrics: List of metric classes

    Returns:
        Dict mapping each metric to its dependencies
    """
    graph: dict[Type[Metric], list[Type[Metric]]] = {}

    # Add all metrics to graph
    for metric_cls in metrics:
        graph[metric_cls] = metric_cls.depends_on()

    # Ensure all dependencies are in the graph
    for metric_cls in list(graph.keys()):
        for dep in graph[metric_cls]:
            if dep not in graph:
                graph[dep] = dep.depends_on()

    return graph
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_graph.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/checkup/graph.py tests/test_graph.py
git commit -m "feat: add dependency graph building"
```

---

## Task 6: Topological Sort

**Files:**
- Modify: `src/checkup/graph.py`
- Modify: `tests/test_graph.py`

**Step 1: Write failing test for topological sort**

Add to `tests/test_graph.py`:

```python
from checkup.graph import topological_sort


def test_topological_sort_no_deps():
    """Test topological sort with no dependencies."""
    graph = {DummyMetric: []}

    result = topological_sort(graph)

    assert result == [DummyMetric]


def test_topological_sort_with_deps():
    """Test topological sort with dependencies."""
    graph = {
        DummyMetric: [],
        DependentDummyMetric: [DummyMetric]
    }

    result = topological_sort(graph)

    # DummyMetric must come before DependentDummyMetric
    assert result.index(DummyMetric) < result.index(DependentDummyMetric)
    assert len(result) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph.py::test_topological_sort_no_deps -v`
Expected: FAIL with import error

**Step 3: Implement topological_sort**

Add to `src/checkup/graph.py`:

```python
def topological_sort(graph: dict[Type[Metric], list[Type[Metric]]]) -> list[Type[Metric]]:
    """Perform topological sort on dependency graph.

    Args:
        graph: Dependency graph mapping metrics to their dependencies

    Returns:
        List of metrics in topological order (dependencies first)

    Raises:
        ValueError: If graph contains cycles
    """
    # Calculate in-degree for each node
    in_degree = {node: 0 for node in graph}
    for node in graph:
        for dep in graph[node]:
            in_degree[dep] = in_degree.get(dep, 0)

    for node in graph:
        for dep in graph[node]:
            in_degree[node] += 1

    # Queue of nodes with no incoming edges
    queue = [node for node in graph if in_degree[node] == 0]
    result = []

    while queue:
        # Remove node from queue
        node = queue.pop(0)
        result.append(node)

        # For each node that depends on this node
        for other in graph:
            if node in graph[other]:
                in_degree[other] -= 1
                if in_degree[other] == 0:
                    queue.append(other)

    # Check for cycles
    if len(result) != len(graph):
        raise ValueError("Dependency graph contains cycles")

    return result
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_graph.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/checkup/graph.py tests/test_graph.py
git commit -m "feat: add topological sort for dependency resolution"
```

---

## Task 7: Cycle Detection

**Files:**
- Modify: `tests/test_graph.py`
- Modify: `src/checkup/metric.py`

**Step 1: Write failing test for cycle detection**

Add to `tests/test_graph.py`:

```python
import pytest
from checkup.metric import CyclicMetricA, CyclicMetricB


def test_topological_sort_detects_cycles():
    """Test that topological sort detects cycles."""
    graph = {
        CyclicMetricA: [CyclicMetricB],
        CyclicMetricB: [CyclicMetricA]
    }

    with pytest.raises(ValueError, match="cycles"):
        topological_sort(graph)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph.py::test_topological_sort_detects_cycles -v`
Expected: FAIL with import error

**Step 3: Create cyclic test metrics**

Add to `src/checkup/metric.py`:

```python
class CyclicMetricA(Metric):
    """Test metric that creates a cycle with CyclicMetricB."""

    name: str = "cyclic_a"
    description: str = "Cyclic test metric A"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type['Metric']]:
        return [CyclicMetricB]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1


class CyclicMetricB(Metric):
    """Test metric that creates a cycle with CyclicMetricA."""

    name: str = "cyclic_b"
    description: str = "Cyclic test metric B"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type['Metric']]:
        return [CyclicMetricA]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph.py::test_topological_sort_detects_cycles -v`
Expected: PASS (cycle detection already implemented)

**Step 5: Commit**

```bash
git add src/checkup/metric.py tests/test_graph.py
git commit -m "test: add cycle detection test"
```

---

## Task 8: Provider System - Dummy Provider

**Files:**
- Modify: `src/checkup/metric.py`
- Modify: `tests/test_metric.py`

**Step 1: Write test for provider function**

Add to `tests/test_metric.py`:

```python
def test_dummy_provider():
    """Test that dummy provider enriches context."""
    from checkup.metric import dummy_provider

    context = {}
    result = dummy_provider(context)

    assert 'dummy_data' in result
    assert result['dummy_data'] == 100


def test_provider_dummy_metric_has_provider():
    """Test that ProviderDummyMetric declares providers."""
    from checkup.metric import ProviderDummyMetric, dummy_provider

    providers = ProviderDummyMetric.providers()

    assert providers == [dummy_provider]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_metric.py::test_dummy_provider -v`
Expected: FAIL with import error

**Step 3: Implement dummy provider and ProviderDummyMetric**

Add to `src/checkup/metric.py`:

```python
def dummy_provider(context: Context) -> Context:
    """Test provider that adds dummy data to context.

    Args:
        context: Current context

    Returns:
        Context with dummy_data added
    """
    return {**context, 'dummy_data': 100}


class ProviderDummyMetric(Metric):
    """Test metric that uses a provider.

    Uses dummy_provider to get data from context.
    """

    name: str = "provider_dummy"
    description: str = "Uses dummy provider"
    unit: str = "count"

    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        """Return dummy provider."""
        return [dummy_provider]

    def calculate(self, context: Context, metrics: dict) -> None:
        """Get value from context."""
        self.value = context['dummy_data']
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_metric.py -v -k provider`
Expected: All provider tests PASS

**Step 5: Commit**

```bash
git add src/checkup/metric.py tests/test_metric.py
git commit -m "feat: add test provider and ProviderDummyMetric"
```

---

## Task 9: Provider Collection and Deduplication

**Files:**
- Create: `src/checkup/providers.py`
- Create: `tests/test_providers.py`

**Step 1: Write failing test for provider collection**

Create `tests/test_providers.py`:

```python
"""Tests for provider collection and execution."""
from checkup.providers import collect_providers
from checkup.metric import ProviderDummyMetric, DummyMetric, dummy_provider


def test_collect_providers_empty():
    """Test collecting providers from metrics with no providers."""
    providers = collect_providers([DummyMetric])

    assert providers == []


def test_collect_providers_single():
    """Test collecting providers from one metric."""
    providers = collect_providers([ProviderDummyMetric])

    assert providers == [dummy_provider]


def test_collect_providers_deduplication():
    """Test that duplicate providers are deduplicated."""
    # Create another metric that uses the same provider
    class AnotherProviderMetric(ProviderDummyMetric):
        name: str = "another_provider"

    providers = collect_providers([ProviderDummyMetric, AnotherProviderMetric])

    # Should only have one instance of dummy_provider
    assert len(providers) == 1
    assert providers[0] is dummy_provider
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_providers.py::test_collect_providers_empty -v`
Expected: FAIL with import error

**Step 3: Implement collect_providers**

Create `src/checkup/providers.py`:

```python
"""Provider collection and execution utilities."""
from typing import Callable, Type

from checkup.metric import Metric
from checkup.types import Context


def collect_providers(
    metrics: list[Type[Metric]]
) -> list[Callable[[Context], Context]]:
    """Collect and deduplicate providers from metrics.

    Args:
        metrics: List of metric classes

    Returns:
        List of unique provider functions (deduplicated by identity)
    """
    seen = set()
    providers = []

    for metric_cls in metrics:
        for provider in metric_cls.providers():
            provider_id = id(provider)
            if provider_id not in seen:
                seen.add(provider_id)
                providers.append(provider)

    return providers
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_providers.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/checkup/providers.py tests/test_providers.py
git commit -m "feat: add provider collection and deduplication"
```

---

## Task 10: Provider Execution

**Files:**
- Modify: `src/checkup/providers.py`
- Modify: `tests/test_providers.py`

**Step 1: Write failing test for provider execution**

Add to `tests/test_providers.py`:

```python
from checkup.providers import execute_providers


def test_execute_providers_empty():
    """Test executing no providers."""
    context = {'initial': 'data'}
    result = execute_providers([], context)

    assert result == {'initial': 'data'}


def test_execute_providers_single():
    """Test executing a single provider."""
    context = {}
    result = execute_providers([dummy_provider], context)

    assert result == {'dummy_data': 100}


def test_execute_providers_multiple():
    """Test executing multiple providers."""
    def provider_a(ctx: Context) -> Context:
        return {**ctx, 'a': 1}

    def provider_b(ctx: Context) -> Context:
        return {**ctx, 'b': 2}

    context = {}
    result = execute_providers([provider_a, provider_b], context)

    assert result == {'a': 1, 'b': 2}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_providers.py::test_execute_providers_empty -v`
Expected: FAIL with import error

**Step 3: Implement execute_providers**

Add to `src/checkup/providers.py`:

```python
def execute_providers(
    providers: list[Callable[[Context], Context]],
    initial_context: Context
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_providers.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/checkup/providers.py tests/test_providers.py
git commit -m "feat: add provider execution"
```

---

## Task 11: CheckHub Basic Structure

**Files:**
- Create: `src/checkup/hub.py`
- Create: `tests/test_hub.py`

**Step 1: Write failing test for CheckHub creation**

Create `tests/test_hub.py`:

```python
"""Tests for CheckHub main orchestration."""
from checkup.hub import CheckHub
from checkup.metric import DummyMetric


def test_checkhub_creation():
    """Test creating a CheckHub instance."""
    hub = CheckHub()

    assert hub is not None


def test_checkhub_with_metrics():
    """Test registering metrics with CheckHub."""
    hub = CheckHub().with_metrics([DummyMetric])

    assert isinstance(hub, CheckHub)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hub.py::test_checkhub_creation -v`
Expected: FAIL with import error

**Step 3: Implement basic CheckHub**

Create `src/checkup/hub.py`:

```python
"""CheckHub main orchestration."""
from typing import Iterable, Type

from checkup.metric import Metric


class CheckHub:
    """Main entry point for metrics calculation.

    Usage:
        CheckHub()
            .with_metrics([MetricA, MetricB])
            .measure()
            .materialize(HtmlMaterializer())
    """

    def __init__(self):
        """Initialize CheckHub."""
        self._metrics: list[Type[Metric]] = []

    def with_metrics(self, metrics: Iterable[Type[Metric]]) -> 'CheckHub':
        """Register metrics to calculate.

        Args:
            metrics: Iterable of metric classes

        Returns:
            Self for chaining
        """
        self._metrics.extend(metrics)
        return self
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_hub.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/checkup/hub.py tests/test_hub.py
git commit -m "feat: add basic CheckHub structure"
```

---

## Task 12: MeasurementResult

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write failing test for MeasurementResult**

Add to `tests/test_hub.py`:

```python
from checkup.hub import MeasurementResult


def test_measurement_result_creation():
    """Test creating a MeasurementResult."""
    metric = DummyMetric(expected_value=42)
    result = MeasurementResult(metrics=[metric])

    assert len(result.metrics) == 1
    assert result.metrics[0] == metric
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hub.py::test_measurement_result_creation -v`
Expected: FAIL with import error

**Step 3: Implement MeasurementResult**

Add to `src/checkup/hub.py`:

```python
from pydantic import BaseModel


class MeasurementResult(BaseModel):
    """Result of measuring metrics.

    Contains all calculated metrics.
    """

    metrics: list[Metric]

    class Config:
        arbitrary_types_allowed = True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hub.py::test_measurement_result_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/checkup/hub.py tests/test_hub.py
git commit -m "feat: add MeasurementResult"
```

---

## Task 13: CheckHub.measure() - Basic Implementation

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write failing test for basic measure**

Add to `tests/test_hub.py`:

```python
def test_checkhub_measure_simple():
    """Test measuring a single metric with no dependencies."""
    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "dummy"
    assert result.metrics[0].value == 42
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hub.py::test_checkhub_measure_simple -v`
Expected: FAIL - measure() not implemented

**Step 3: Implement basic measure()**

Add to `src/checkup/hub.py`:

```python
from checkup.graph import build_dependency_graph, topological_sort
from checkup.providers import collect_providers, execute_providers
from checkup.types import Context


class CheckHub:
    # ... existing code ...

    def measure(self) -> MeasurementResult:
        """Execute providers and calculate all metrics.

        Returns:
            MeasurementResult containing calculated metrics
        """
        # Build context
        context: Context = {}

        # Collect and execute providers
        providers = collect_providers(self._metrics)
        context = execute_providers(providers, context)

        # Build dependency graph and sort
        graph = build_dependency_graph(self._metrics)
        ordered_metrics = topological_sort(graph)

        # Calculate metrics in order
        calculated: dict[Type[Metric], Metric] = {}

        for metric_cls in ordered_metrics:
            # Instantiate metric (no config yet)
            metric = metric_cls()

            # Calculate
            metric.calculate(context, calculated)

            # Cache
            calculated[metric_cls] = metric

        # Return result
        return MeasurementResult(metrics=list(calculated.values()))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hub.py::test_checkhub_measure_simple -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/checkup/hub.py tests/test_hub.py
git commit -m "feat: implement basic CheckHub.measure()"
```

---

## Task 14: CheckHub.measure() - With Dependencies

**Files:**
- Modify: `tests/test_hub.py`

**Step 1: Write failing test for dependent metrics**

Add to `tests/test_hub.py`:

```python
from checkup.metric import DependentDummyMetric


def test_checkhub_measure_with_dependencies():
    """Test measuring metrics with dependencies."""
    result = (
        CheckHub()
        .with_metrics([DependentDummyMetric])  # DummyMetric added automatically
        .measure()
    )

    # Should have both metrics
    assert len(result.metrics) == 2

    # Find metrics by name
    metrics_by_name = {m.name: m for m in result.metrics}

    assert 'dummy' in metrics_by_name
    assert 'dependent_dummy' in metrics_by_name

    # Verify values
    assert metrics_by_name['dummy'].value == 42
    assert metrics_by_name['dependent_dummy'].value == 84  # 42 * 2
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_hub.py::test_checkhub_measure_with_dependencies -v`
Expected: PASS (already implemented)

**Step 3: Commit**

```bash
git add tests/test_hub.py
git commit -m "test: add dependency resolution test"
```

---

## Task 15: CheckHub.measure() - With Providers

**Files:**
- Modify: `tests/test_hub.py`

**Step 1: Write failing test for metrics with providers**

Add to `tests/test_hub.py`:

```python
from checkup.metric import ProviderDummyMetric


def test_checkhub_measure_with_providers():
    """Test measuring metrics that use providers."""
    result = (
        CheckHub()
        .with_metrics([ProviderDummyMetric])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "provider_dummy"
    assert result.metrics[0].value == 100  # From dummy_provider
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_hub.py::test_checkhub_measure_with_providers -v`
Expected: PASS (already implemented)

**Step 3: Commit**

```bash
git add tests/test_hub.py
git commit -m "test: add provider execution test"
```

---

## Task 16: YAML Config Loading

**Files:**
- Create: `src/checkup/config.py`
- Create: `tests/test_config.py`
- Create: `tests/fixtures/checkup.yaml`

**Step 1: Write failing test for YAML loading**

Create `tests/test_config.py`:

```python
"""Tests for YAML configuration loading."""
from pathlib import Path
from checkup.config import load_config


def test_load_config(tmp_path):
    """Test loading metric configs from YAML."""
    # Create test YAML
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  dummy:
    expected_value: 100
  python_version:
    min: "3.11.0"
    max: "3.12.99"
""")

    config = load_config(config_file)

    assert 'dummy' in config
    assert config['dummy']['expected_value'] == 100
    assert config['python_version']['min'] == '3.11.0'


def test_load_config_missing_file():
    """Test loading config when file doesn't exist."""
    config = load_config(Path("nonexistent.yaml"))

    assert config == {}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_config -v`
Expected: FAIL with import error

**Step 3: Add PyYAML dependency**

Modify `pyproject.toml` to add:

```toml
dependencies = [
    "pydantic>=2.11.7",
    "pyyaml>=6.0",
]
```

Run: `uv pip install -e .`

**Step 4: Implement load_config**

Create `src/checkup/config.py`:

```python
"""YAML configuration loading."""
from pathlib import Path
from typing import Any
import yaml


def load_config(config_path: Path) -> dict[str, dict[str, Any]]:
    """Load metric configurations from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Dict mapping metric names to their config dicts
        Empty dict if file doesn't exist
    """
    if not config_path.exists():
        return {}

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data or 'metrics' not in data:
        return {}

    return data['metrics']
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add pyproject.toml src/checkup/config.py tests/test_config.py
git commit -m "feat: add YAML config loading"
```

---

## Task 17: CheckHub - Integrate Config Loading

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`
- Create: `tests/fixtures/test_config.yaml`

**Step 1: Write failing test for config integration**

Create `tests/fixtures/test_config.yaml`:

```yaml
metrics:
  dummy:
    expected_value: 200
```

Add to `tests/test_hub.py`:

```python
from pathlib import Path


def test_checkhub_measure_with_config():
    """Test measuring metrics with YAML config."""
    config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"

    result = (
        CheckHub(config_path=config_path)
        .with_metrics([DummyMetric])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 200  # From YAML, not default 42
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hub.py::test_checkhub_measure_with_config -v`
Expected: FAIL - config_path not supported

**Step 3: Update CheckHub to support config**

Modify `src/checkup/hub.py`:

```python
from pathlib import Path
from typing import Optional
from checkup.config import load_config


class CheckHub:
    """Main entry point for metrics calculation."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize CheckHub.

        Args:
            config_path: Optional path to YAML config file
        """
        self._metrics: list[Type[Metric]] = []
        self._config_path = config_path

    # ... existing with_metrics ...

    def measure(self) -> MeasurementResult:
        """Execute providers and calculate all metrics."""
        # Load config
        metric_configs = {}
        if self._config_path:
            metric_configs = load_config(self._config_path)

        # Build context
        context: Context = {}

        # Collect and execute providers
        providers = collect_providers(self._metrics)
        context = execute_providers(providers, context)

        # Build dependency graph and sort
        graph = build_dependency_graph(self._metrics)
        ordered_metrics = topological_sort(graph)

        # Calculate metrics in order
        calculated: dict[Type[Metric], Metric] = {}

        for metric_cls in ordered_metrics:
            # Get config for this metric
            config = metric_configs.get(metric_cls().name, {})

            # Instantiate metric with config
            metric = metric_cls(**config)

            # Calculate
            metric.calculate(context, calculated)

            # Cache
            calculated[metric_cls] = metric

        # Return result
        return MeasurementResult(metrics=list(calculated.values()))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hub.py::test_checkhub_measure_with_config -v`
Expected: PASS

**Step 5: Run all tests to verify nothing broke**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/checkup/hub.py tests/test_hub.py tests/fixtures/test_config.yaml
git commit -m "feat: integrate YAML config into CheckHub"
```

---

## Task 18: Materializer ABC

**Files:**
- Create: `src/checkup/materializers.py`
- Create: `tests/test_materializers.py`

**Step 1: Write failing test for Materializer ABC**

Create `tests/test_materializers.py`:

```python
"""Tests for materializers."""
from checkup.materializers import Materializer
from checkup.metric import DummyMetric


def test_materializer_is_abstract():
    """Test that Materializer cannot be instantiated."""
    import pytest

    with pytest.raises(TypeError):
        Materializer()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_materializers.py::test_materializer_is_abstract -v`
Expected: FAIL with import error

**Step 3: Implement Materializer ABC**

Create `src/checkup/materializers.py`:

```python
"""Materializers for outputting metrics."""
from abc import ABC, abstractmethod
from pydantic import BaseModel

from checkup.metric import Metric


class Materializer(ABC, BaseModel):
    """Base class for metric materializers.

    Materializers format and output metrics to various formats.
    """

    @abstractmethod
    def materialize(self, metrics: list[Metric]) -> None:
        """Format and output metrics.

        Args:
            metrics: List of calculated metrics
        """
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_materializers.py::test_materializer_is_abstract -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/checkup/materializers.py tests/test_materializers.py
git commit -m "feat: add Materializer ABC"
```

---

## Task 19: ConsoleMaterializer

**Files:**
- Modify: `src/checkup/materializers.py`
- Modify: `tests/test_materializers.py`

**Step 1: Write failing test for ConsoleMaterializer**

Add to `tests/test_materializers.py`:

```python
from checkup.materializers import ConsoleMaterializer
from io import StringIO
import sys


def test_console_materializer():
    """Test console output materializer."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    materializer = ConsoleMaterializer()
    materializer.materialize([metric])

    # Reset stdout
    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert 'dummy' in output
    assert '42' in output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_materializers.py::test_console_materializer -v`
Expected: FAIL with import error

**Step 3: Implement ConsoleMaterializer**

Add to `src/checkup/materializers.py`:

```python
class ConsoleMaterializer(Materializer):
    """Output metrics to console.

    Simple text output for debugging and quick checks.
    """

    def materialize(self, metrics: list[Metric]) -> None:
        """Print metrics to console."""
        print("\n=== Metrics Report ===\n")

        for metric in metrics:
            print(f"{metric.name}: {metric.value} {metric.unit}")
            if metric.description:
                print(f"  {metric.description}")
            print()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_materializers.py::test_console_materializer -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/checkup/materializers.py tests/test_materializers.py
git commit -m "feat: add ConsoleMaterializer"
```

---

## Task 20: MeasurementResult.materialize()

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write failing test for materialize**

Add to `tests/test_hub.py`:

```python
from checkup.materializers import ConsoleMaterializer
from io import StringIO
import sys


def test_measurement_result_materialize():
    """Test materializing measurement results."""
    captured_output = StringIO()
    sys.stdout = captured_output

    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .measure()
        .materialize(ConsoleMaterializer())
    )

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert 'dummy' in output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hub.py::test_measurement_result_materialize -v`
Expected: FAIL - materialize not implemented

**Step 3: Implement MeasurementResult.materialize()**

Add to `src/checkup/hub.py`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkup.materializers import Materializer


class MeasurementResult(BaseModel):
    """Result of measuring metrics."""

    metrics: list[Metric]

    class Config:
        arbitrary_types_allowed = True

    def materialize(self, materializer: 'Materializer') -> None:
        """Output results using materializer.

        Args:
            materializer: Materializer instance for output
        """
        materializer.materialize(self.metrics)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hub.py::test_measurement_result_materialize -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/checkup/hub.py tests/test_hub.py
git commit -m "feat: implement MeasurementResult.materialize()"
```

---

## Task 21: Update Package Exports

**Files:**
- Modify: `src/checkup/__init__.py`

**Step 1: Update __init__.py exports**

Modify `src/checkup/__init__.py`:

```python
"""Checkup - Extensible metrics calculation framework."""
from checkup.hub import CheckHub, MeasurementResult
from checkup.metric import Metric
from checkup.materializers import Materializer, ConsoleMaterializer
from checkup.types import Context

__all__ = [
    'CheckHub',
    'MeasurementResult',
    'Metric',
    'Materializer',
    'ConsoleMaterializer',
    'Context',
]


def main() -> None:
    """CLI entry point."""
    print("Checkup metrics framework")
    print("Import CheckHub to get started")
```

**Step 2: Test imports**

Run: `python -c "from checkup import CheckHub, Metric, ConsoleMaterializer"`
Expected: No errors

**Step 3: Commit**

```bash
git add src/checkup/__init__.py
git commit -m "feat: update package exports"
```

---

## Task 22: Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write comprehensive integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for the full metrics pipeline."""
from pathlib import Path
from checkup import CheckHub, Metric, ConsoleMaterializer
from checkup.types import Context


def test_full_pipeline(tmp_path):
    """Test complete pipeline: config, providers, dependencies, calculation, output."""

    # Create config
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  base_metric:
    threshold: 50
  derived_metric:
    multiplier: 3
""")

    # Define test provider
    def test_provider(context: Context) -> Context:
        return {**context, 'base_value': 25}

    # Define test metrics
    class BaseMetric(Metric):
        name: str = "base_metric"
        description: str = "Base test metric"
        unit: str = "units"
        threshold: int = 100

        @classmethod
        def providers(cls):
            return [test_provider]

        def calculate(self, context: Context, metrics: dict) -> None:
            self.value = context['base_value']

    class DerivedMetric(Metric):
        name: str = "derived_metric"
        description: str = "Derived test metric"
        unit: str = "units"
        multiplier: int = 2

        @classmethod
        def depends_on(cls):
            return [BaseMetric]

        def calculate(self, context: Context, metrics: dict) -> None:
            base = metrics[BaseMetric].value
            self.value = base * self.multiplier

    # Run pipeline
    result = (
        CheckHub(config_path=config_file)
        .with_metrics([DerivedMetric])  # BaseMetric added automatically
        .measure()
    )

    # Verify results
    metrics_by_name = {m.name: m for m in result.metrics}

    assert metrics_by_name['base_metric'].value == 25
    assert metrics_by_name['base_metric'].threshold == 50  # From config

    assert metrics_by_name['derived_metric'].value == 75  # 25 * 3
    assert metrics_by_name['derived_metric'].multiplier == 3  # From config
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add comprehensive integration test"
```

---

## Task 23: Run Full Test Suite

**Files:**
- None (verification step)

**Step 1: Run all tests with coverage**

Run: `pytest tests/ -v --cov=checkup --cov-report=term-missing`
Expected: All tests PASS, good coverage

**Step 2: Verify test metrics**

Expected output similar to:
- tests/test_config.py: PASS
- tests/test_graph.py: PASS
- tests/test_hub.py: PASS
- tests/test_integration.py: PASS
- tests/test_materializers.py: PASS
- tests/test_metric.py: PASS
- tests/test_providers.py: PASS

**Step 3: Fix any failing tests**

If any tests fail, investigate and fix before proceeding.

---

## Task 24: Documentation

**Files:**
- Modify: `README.md`

**Step 1: Write comprehensive README**

Modify `README.md`:

```markdown
# Checkup

Extensible metrics calculation framework with dependency resolution and context enrichment.

## Features

- **Extensible metrics** - Define custom metrics as Pydantic models
- **Dependency resolution** - Metrics can depend on other metrics
- **Context providers** - Enrich context from environment (credentials, configs)
- **YAML configuration** - Configure metric bounds and parameters
- **Multiple outputs** - Materialize to console, HTML, CSV, etc.
- **Type-safe** - Full type hints and Pydantic validation

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from checkup import CheckHub, Metric, ConsoleMaterializer
from checkup.types import Context

# Define a metric
class PythonVersionMetric(Metric):
    name: str = "python_version"
    description: str = "Python version check"
    unit: str = "version"
    min: str = "3.11.0"

    def calculate(self, context: Context, metrics: dict) -> None:
        import sys
        self.value = f"{sys.version_info.major}.{sys.version_info.minor}"

# Run metrics
result = (
    CheckHub()
    .with_metrics([PythonVersionMetric])
    .measure()
    .materialize(ConsoleMaterializer())
)
```

## Configuration

Create `checkup.yaml`:

```yaml
metrics:
  python_version:
    min: "3.11.0"
    max: "3.12.99"
```

Use with CheckHub:

```python
CheckHub(config_path=Path("checkup.yaml"))
```

## Architecture

See [Design Document](docs/plans/2025-12-15-metrics-framework-design.md) for details.

### Key Concepts

- **Metrics** - Calculate values from context
- **Providers** - Functions that enrich context (shared across metrics)
- **Dependencies** - Metrics can depend on other metrics' values
- **Materializers** - Output formats (Console, HTML, CSV, etc.)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=checkup
```

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 25: Final Verification

**Files:**
- None (verification step)

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 2: Verify package structure**

Run: `tree src/checkup`
Expected:
```
src/checkup/
├── __init__.py
├── config.py
├── graph.py
├── hub.py
├── materializers.py
├── metric.py
├── providers.py
└── types.py
```

**Step 3: Test package import**

Run:
```python
python -c "
from checkup import CheckHub, Metric
from checkup.metric import DummyMetric

result = CheckHub().with_metrics([DummyMetric]).measure()
print(f'Success! Calculated {len(result.metrics)} metrics')
"
```

Expected: "Success! Calculated 1 metrics"

**Step 4: Create final commit**

```bash
git add -A
git commit -m "feat: complete metrics framework implementation

- Metric ABC with Pydantic validation
- Dependency resolution via topological sort
- Provider system for context enrichment
- YAML configuration loading
- CheckHub orchestration
- ConsoleMaterializer for output
- Comprehensive test suite

All tests passing. Framework ready for use."
```

---

## Next Steps

After completing this implementation plan:

1. **Add more materializers** - HTML, CSV, SQL implementations
2. **Error handling improvements** - Better error messages, validation
3. **Plugin system** - Dynamic loading of external metrics
4. **Performance** - Async providers, parallel calculation
5. **CLI tool** - Command-line interface for running metrics

## Notes

- All tasks follow TDD: test first, run to fail, implement, run to pass, commit
- Each commit is small and focused
- Tests provide comprehensive coverage
- Type hints throughout for IDE support
- Pydantic provides validation and serialization
