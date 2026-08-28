# Multi-Context Metric Calculation Implementation Plan

## Overview

Add support for calculating metrics across multiple contexts (e.g., 100+ file paths) with:
- Config loaded once
- Parallel execution across contexts
- Single materialization of aggregated results
- Context info merged into metric tags

## Design Decisions

| Decision | Choice |
|----------|--------|
| Context identification | Tags: `metric.tags.update(context_dict)` |
| API trigger | Fluent: `.with_contexts([...])` |
| Parallelism | Configurable: `measure(max_workers=None)`, None = all CPUs |
| Error handling | Skip and continue: `result.metrics` + `result.errors` |
| Context type | Generic dict - all keys merged into tags |

## Target API

```python
result = (
    CheckHub(config_path=Path("checkup.yaml"))
    .with_metrics([MetricA, MetricB])
    .with_contexts([
        {"path": "/repo1", "env": "prod"},
        {"path": "/repo2", "env": "staging"},
        # ... 100+ contexts
    ])
    .measure(max_workers=None)  # None = use all CPUs
)

# Successful metrics - flat list with context in tags
for metric in result.metrics:
    print(f"{metric.name} @ {metric.tags['path']}: {metric.value}")

# Failed contexts
for context, error in result.errors:
    print(f"Failed {context['path']}: {error}")

# Single materialization
result.materialize(CSVMaterializer(output_path=Path("report.csv")))
```

---

## Task 1: Add ContextDict Type Alias

**Files:**
- Modify: `src/checkup/types.py`

**Step 1: Add type alias**

```python
# In src/checkup/types.py, add after Context:
ContextDict = dict[str, Any]
```

**Verification:**
```bash
uv run python -c "from checkup.types import ContextDict; print('OK')"
```

---

## Task 2: Update MeasurementResult to Include Errors

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write failing test**

Add to `tests/test_hub.py`:

```python
def test_measurement_result_with_errors():
    """Test MeasurementResult can hold errors."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    errors = [
        ({"path": "/bad/path"}, ValueError("Path not found"))
    ]

    result = MeasurementResult(metrics=[metric], errors=errors)

    assert len(result.metrics) == 1
    assert len(result.errors) == 1
    assert result.errors[0][0] == {"path": "/bad/path"}
```

**Step 2: Update MeasurementResult**

Modify `src/checkup/hub.py`:

```python
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
```

**Verification:**
```bash
uv run pytest tests/test_hub.py::test_measurement_result_with_errors -v
```

---

## Task 3: Add with_contexts() Method

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write failing test**

Add to `tests/test_hub.py`:

```python
def test_checkhub_with_contexts():
    """Test registering contexts with CheckHub."""
    hub = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_contexts([{"path": "/repo1"}, {"path": "/repo2"}])
    )

    assert isinstance(hub, CheckHub)
    assert len(hub._contexts) == 2
```

**Step 2: Add _contexts attribute and with_contexts method**

Modify `src/checkup/hub.py` CheckHub class:

```python
def __init__(self, config_path: Path | None = None) -> None:
    """Initialize CheckHub.

    Args:
        config_path: Optional path to YAML config file
    """
    self._metrics: list[Type[Metric]] = []
    self._contexts: list[dict[str, Any]] = []
    self._config_path = config_path

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
```

**Verification:**
```bash
uv run pytest tests/test_hub.py::test_checkhub_with_contexts -v
```

---

## Task 4: Extract Single-Context Calculation Method

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write test for internal method**

Add to `tests/test_hub.py`:

```python
def test_checkhub_measure_single_context():
    """Test _measure_single_context internal method."""
    hub = CheckHub().with_metrics([DummyMetric])

    # Pre-compute shared state
    from checkup.graph import build_dependency_graph, topological_sort
    graph = build_dependency_graph(hub._metrics)
    execution_order = topological_sort(graph)
    providers = hub._collect_providers(list(execution_order))
    direct_metrics = set(hub._metrics)

    context_dict = {"path": "/test/repo", "env": "test"}

    metrics = hub._measure_single_context(
        context_dict=context_dict,
        execution_order=execution_order,
        providers=providers,
        direct_metrics=direct_metrics,
        metric_configs={},
    )

    assert len(metrics) == 1
    assert metrics[0].name == "dummy"
    assert metrics[0].tags["path"] == "/test/repo"
    assert metrics[0].tags["env"] == "test"
```

**Step 2: Extract _measure_single_context method**

Add to CheckHub class in `src/checkup/hub.py`:

```python
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
    # Initialize context from context_dict
    context: Context = context_dict.copy()

    # Execute providers
    context = self._execute_providers(providers, context)

    # Calculate metrics in order
    calculated: dict[Type[Metric], Metric] = {}
    result_metrics: list[Metric] = []

    for metric_cls in execution_order:
        # Get config for this metric by name
        config = metric_configs.get(metric_cls().name, {})  # type: ignore
        # Instantiate with config
        metric = metric_cls(**config, is_direct=(metric_cls in direct_metrics))
        # Merge context_dict into tags
        metric.tags.update(context_dict)
        # Calculate
        metric.calculate(context, calculated)
        calculated[metric_cls] = metric
        result_metrics.append(metric)

    return result_metrics
```

**Verification:**
```bash
uv run pytest tests/test_hub.py::test_checkhub_measure_single_context -v
```

---

## Task 5: Implement Multi-Context measure() with Parallelism

**Files:**
- Modify: `src/checkup/hub.py`
- Modify: `tests/test_hub.py`

**Step 1: Write failing test for multi-context**

Add to `tests/test_hub.py`:

```python
def test_checkhub_measure_multiple_contexts():
    """Test measuring metrics across multiple contexts."""
    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_contexts([
            {"path": "/repo1"},
            {"path": "/repo2"},
            {"path": "/repo3"},
        ])
        .measure()
    )

    # 3 contexts × 1 metric = 3 results
    assert len(result.metrics) == 3
    assert len(result.errors) == 0

    paths = {m.tags["path"] for m in result.metrics}
    assert paths == {"/repo1", "/repo2", "/repo3"}

    # All metrics should have correct value
    for metric in result.metrics:
        assert metric.value == 42
```

**Step 2: Write test for parallel execution**

Add to `tests/test_hub.py`:

```python
def test_checkhub_measure_parallel():
    """Test parallel execution with max_workers."""
    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_contexts([{"path": f"/repo{i}"} for i in range(10)])
        .measure(max_workers=4)
    )

    assert len(result.metrics) == 10
    assert len(result.errors) == 0
```

**Step 3: Write test for error handling**

Add to `tests/test_hub.py`:

```python
def test_checkhub_measure_with_failing_context():
    """Test that failing contexts are captured in errors."""
    from checkup.metric import Metric
    from checkup.types import Context

    class FailingMetric(Metric):
        name: str = "failing"
        description: str = "Always fails"
        unit: str = "count"

        def calculate(self, context: Context, metrics: dict) -> None:
            if context.get("should_fail"):
                raise ValueError("Intentional failure")
            self.value = 1

    result = (
        CheckHub()
        .with_metrics([FailingMetric])
        .with_contexts([
            {"path": "/good", "should_fail": False},
            {"path": "/bad", "should_fail": True},
            {"path": "/also_good", "should_fail": False},
        ])
        .measure()
    )

    # 2 successful, 1 failed
    assert len(result.metrics) == 2
    assert len(result.errors) == 1

    # Error contains context and exception
    failed_context, error = result.errors[0]
    assert failed_context["path"] == "/bad"
    assert "Intentional failure" in str(error)
```

**Step 4: Update measure() method**

Modify `measure()` in `src/checkup/hub.py`:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

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
    # Step 1: Load config (once)
    metric_configs: dict = {}
    if self._config_path:
        metric_configs = load_config(self._config_path)

    # Step 2: Build dependency graph and get execution order (once)
    graph = build_dependency_graph(self._metrics)
    execution_order = topological_sort(graph)

    # Step 3: Collect providers (once)
    providers = self._collect_providers(list(execution_order))
    direct_metrics = set(self._metrics)

    # Step 4: Determine contexts to process
    if self._contexts:
        contexts = self._contexts
    else:
        # Backward compatibility: single context mode
        contexts = [initial_context.copy() if initial_context else {}]

    # Step 5: Process contexts (parallel if multiple)
    all_metrics: list[Metric] = []
    all_errors: list[tuple[dict, Exception]] = []

    if len(contexts) == 1:
        # Single context - no parallelism needed
        try:
            metrics = self._measure_single_context(
                context_dict=contexts[0],
                execution_order=execution_order,
                providers=providers,
                direct_metrics=direct_metrics,
                metric_configs=metric_configs,
            )
            all_metrics.extend(metrics)
        except Exception as e:
            all_errors.append((contexts[0], e))
    else:
        # Multiple contexts - use thread pool
        workers = max_workers if max_workers is not None else os.cpu_count()

        with ThreadPoolExecutor(max_workers=workers) as executor:
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
                    metrics = future.result()
                    all_metrics.extend(metrics)
                except Exception as e:
                    all_errors.append((ctx, e))

    return MeasurementResult(metrics=all_metrics, errors=all_errors)
```

**Verification:**
```bash
uv run pytest tests/test_hub.py::test_checkhub_measure_multiple_contexts -v
uv run pytest tests/test_hub.py::test_checkhub_measure_parallel -v
uv run pytest tests/test_hub.py::test_checkhub_measure_with_failing_context -v
```

---

## Task 6: Ensure Backward Compatibility

**Files:**
- Modify: `tests/test_hub.py`

**Step 1: Verify existing tests still pass**

All existing tests should continue to work because:
- `with_contexts()` is optional
- When no contexts registered, uses `initial_context` parameter (backward compatible)
- `MeasurementResult.errors` defaults to empty list

**Verification:**
```bash
uv run pytest tests/test_hub.py -v
```

---

## Task 7: Add Integration Test for Multi-Context

**Files:**
- Modify: `tests/test_integration.py`

**Step 1: Add comprehensive integration test**

Add to `tests/test_integration.py`:

```python
def test_multi_context_pipeline(tmp_path):
    """Test complete multi-context pipeline with config, providers, and materialization."""
    from pathlib import Path

    # Create config
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  path_metric:
    multiplier: 2
""")

    # Define provider that uses path from context
    def path_provider(context: Context) -> Context:
        path = context.get("path", "/unknown")
        return {**context, "path_length": len(path)}

    # Define metric that uses provider data
    class PathMetric(Metric):
        name: str = "path_metric"
        description: str = "Calculates based on path"
        unit: str = "count"
        multiplier: int = 1

        @classmethod
        def providers(cls):
            return [path_provider]

        def calculate(self, context: Context, metrics: dict) -> None:
            self.value = context["path_length"] * self.multiplier

    # Run with multiple contexts
    result = (
        CheckHub(config_path=config_file)
        .with_metrics([PathMetric])
        .with_contexts([
            {"path": "/short"},       # len=6, * 2 = 12
            {"path": "/medium/path"}, # len=12, * 2 = 24
            {"path": "/very/long/path/here"},  # len=20, * 2 = 40
        ])
        .measure(max_workers=2)
    )

    assert len(result.metrics) == 3
    assert len(result.errors) == 0

    # Verify values and context tags
    metrics_by_path = {m.tags["path"]: m for m in result.metrics}

    assert metrics_by_path["/short"].value == 12
    assert metrics_by_path["/medium/path"].value == 24
    assert metrics_by_path["/very/long/path/here"].value == 40

    # Test materialization to CSV
    csv_path = tmp_path / "results.csv"
    result.materialize(CSVMaterializer(output_path=csv_path, include_indirect=True))

    content = csv_path.read_text()
    assert "/short" in content
    assert "/medium/path" in content
```

**Verification:**
```bash
uv run pytest tests/test_integration.py::test_multi_context_pipeline -v
```

---

## Task 8: Update Package Exports

**Files:**
- Modify: `src/checkup/__init__.py`
- Modify: `src/checkup/types.py`

**Step 1: Export ContextDict type**

Add to `src/checkup/types.py`:
```python
ContextDict = dict[str, Any]
```

Add to `src/checkup/__init__.py`:
```python
from checkup.types import Context, ContextDict

__all__ = [
    # ... existing exports ...
    "ContextDict",
]
```

**Verification:**
```bash
uv run python -c "from checkup import CheckHub, ContextDict; print('OK')"
```

---

## Task 9: Run Full Test Suite

**Verification:**
```bash
uv run pytest tests/ -v
```

All tests should pass.

---

## Summary

After completing all tasks, the API will support:

```python
# Single context (backward compatible)
CheckHub().with_metrics([M]).measure()
CheckHub().with_metrics([M]).measure({"key": "value"})

# Multi-context with parallelism
CheckHub()
    .with_metrics([MetricA, MetricB])
    .with_contexts([
        {"path": "/repo1", "env": "prod"},
        {"path": "/repo2", "env": "dev"},
        # ... 100+ contexts
    ])
    .measure(max_workers=None)  # Auto-detect CPUs

# Results
result.metrics   # Flat list, context in tags
result.errors    # [(context_dict, exception), ...]
```
