# Instance-Based Providers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor providers from classmethod-based to instance-based, replace `with_contexts()` with `with_providers()`.

**Architecture:** Providers become instantiable classes with config in `__init__` and a `provide(self)` method. TagProvider is a special provider whose output merges into metric tags. The hub validates that all required providers are present before execution.

**Tech Stack:** Python 3.12, Pydantic, pytest

---

## Task 1: Update Provider Base Class

**Files:**
- Modify: `src/checkup/provider.py`
- Test: `tests/test_provider.py`

**Step 1: Write failing tests for new Provider interface**

In `tests/test_provider.py`, replace the entire file:

```python
"""Tests for Provider base class."""

from typing import Any, ClassVar

import pytest

from checkup.provider import Provider


class TestProviderBaseClass:
    """Tests for the Provider abstract base class."""

    def test_provider_is_abstract(self):
        """Test that Provider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Provider()

    def test_provider_subclass_must_define_name(self):
        """Test that Provider subclass must have a name attribute."""

        class NoNameProvider(Provider):
            def provide(self) -> dict[str, Any]:
                return {}

        provider = NoNameProvider()
        with pytest.raises(AttributeError):
            _ = provider.name

    def test_provider_subclass_must_implement_provide(self):
        """Test that Provider subclass must implement provide method."""

        class NoProvideProvider(Provider):
            name: ClassVar[str] = "no_provide"

        with pytest.raises(TypeError):
            NoProvideProvider()

    def test_valid_provider_subclass(self):
        """Test that a valid Provider subclass works correctly."""

        class ValidProvider(Provider):
            name: ClassVar[str] = "valid"

            def __init__(self, value: str = "default"):
                self.value = value

            def provide(self) -> dict[str, Any]:
                return {"key": self.value}

        provider = ValidProvider(value="custom")
        result = provider.provide()
        assert result == {"key": "custom"}
        assert provider.name == "valid"

    def test_provider_with_no_args(self):
        """Test provider that takes no constructor arguments."""

        class SimpleProvider(Provider):
            name: ClassVar[str] = "simple"

            def provide(self) -> dict[str, Any]:
                return {"static": "data"}

        provider = SimpleProvider()
        assert provider.provide() == {"static": "data"}
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_provider.py -v`
Expected: FAIL - tests expect instance method but current code has classmethod

**Step 3: Update Provider base class**

Replace `src/checkup/provider.py`:

```python
"""Provider base class for context enrichment."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Provider(ABC):
    """Base class for context providers.

    Providers enrich the context with data that metrics can use.
    Each provider adds data under its own namespace in the context.

    Subclasses must:
        - Define a `name` class attribute (the namespace)
        - Implement the `provide()` instance method
        - Accept configuration in `__init__`

    Example:
        class DatabaseProvider(Provider):
            name: ClassVar[str] = "database"

            def __init__(self, connection_string: str):
                self.connection_string = connection_string

            def provide(self) -> dict[str, Any]:
                conn = connect(self.connection_string)
                return {"connection": conn}

    The framework adds the returned dict under context[provider.name].
    """

    name: ClassVar[str]

    @abstractmethod
    def provide(self) -> dict[str, Any]:
        """Generate data to add to context under this provider's namespace.

        Returns:
            Dict of data to add under context[cls.name]
        """
        ...
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_provider.py -v`
Expected: PASS

---

## Task 2: Add TagProvider

**Files:**
- Create: `src/checkup/providers/tags.py`
- Modify: `src/checkup/providers/__init__.py`
- Test: `tests/test_tag_provider.py`

**Step 1: Write failing tests for TagProvider**

Create `tests/test_tag_provider.py`:

```python
"""Tests for TagProvider."""

from checkup.providers.tags import TagProvider


class TestTagProvider:
    """Tests for TagProvider special provider."""

    def test_tag_provider_has_correct_name(self):
        """Test TagProvider has name 'tags'."""
        provider = TagProvider(env="prod")
        assert provider.name == "tags"

    def test_tag_provider_stores_kwargs(self):
        """Test TagProvider stores kwargs as tags."""
        provider = TagProvider(env="prod", team="data")
        assert provider.tags == {"env": "prod", "team": "data"}

    def test_tag_provider_provide_returns_tags(self):
        """Test provide() returns the tags dict."""
        provider = TagProvider(env="prod", team="data")
        result = provider.provide()
        assert result == {"env": "prod", "team": "data"}

    def test_tag_provider_empty_tags(self):
        """Test TagProvider with no tags."""
        provider = TagProvider()
        assert provider.provide() == {}

    def test_tag_provider_various_value_types(self):
        """Test TagProvider accepts various value types."""
        provider = TagProvider(count=42, enabled=True, ratio=0.5)
        result = provider.provide()
        assert result == {"count": 42, "enabled": True, "ratio": 0.5}
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tag_provider.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Implement TagProvider**

Create `src/checkup/providers/tags.py`:

```python
"""TagProvider for adding arbitrary tags to metrics."""

from typing import Any, ClassVar

from checkup.provider import Provider


class TagProvider(Provider):
    """Special provider for adding tags to metrics.

    Unlike regular providers, TagProvider's data is auto-merged
    into metric.tags by the framework rather than added to context.

    Example:
        hub.with_providers([
            [DbtProvider(path="./manifest.json"), TagProvider(env="prod", team="data")]
        ])
    """

    name: ClassVar[str] = "tags"

    def __init__(self, **tags: Any):
        """Initialize with arbitrary key-value tags.

        Args:
            **tags: Key-value pairs to add as metric tags
        """
        self.tags = tags

    def provide(self) -> dict[str, Any]:
        """Return tags dict.

        Returns:
            Dict of tags to merge into metric.tags
        """
        return self.tags
```

**Step 4: Update providers __init__.py**

Replace `src/checkup/providers/__init__.py`:

```python
"""Built-in providers for checkup."""

from checkup.providers.tags import TagProvider

__all__ = ["TagProvider"]
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_tag_provider.py -v`
Expected: PASS

---

## Task 3: Update CheckHub with_providers Method

**Files:**
- Modify: `src/checkup/hub.py`
- Test: `tests/test_hub_with_providers.py`

**Step 1: Write failing tests for with_providers**

Create `tests/test_hub_with_providers.py`:

```python
"""Tests for CheckHub.with_providers() method."""

from typing import Any, ClassVar

from checkup.hub import CheckHub
from checkup.provider import Provider
from checkup.providers.tags import TagProvider


class SimpleProvider(Provider):
    """Test provider with simple data."""

    name: ClassVar[str] = "simple"

    def __init__(self, value: int = 10):
        self.value = value

    def provide(self) -> dict[str, Any]:
        return {"value": self.value}


class TestWithProviders:
    """Tests for with_providers method."""

    def test_with_providers_stores_provider_sets(self):
        """Test that with_providers stores provider sets."""
        hub = CheckHub().with_providers([
            [SimpleProvider(value=1)],
            [SimpleProvider(value=2)],
        ])

        assert len(hub._provider_sets) == 2
        assert hub._provider_sets[0][0].value == 1
        assert hub._provider_sets[1][0].value == 2

    def test_with_providers_accepts_iterables(self):
        """Test that with_providers accepts any iterables."""
        hub = CheckHub().with_providers([
            (SimpleProvider(), TagProvider(env="prod")),
        ])

        assert len(hub._provider_sets) == 1
        assert len(hub._provider_sets[0]) == 2

    def test_with_providers_returns_self(self):
        """Test that with_providers returns self for chaining."""
        hub = CheckHub()
        result = hub.with_providers([[SimpleProvider()]])
        assert result is hub

    def test_with_providers_accumulates(self):
        """Test that multiple with_providers calls accumulate."""
        hub = (
            CheckHub()
            .with_providers([[SimpleProvider(value=1)]])
            .with_providers([[SimpleProvider(value=2)]])
        )

        assert len(hub._provider_sets) == 2
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_hub_with_providers.py -v`
Expected: FAIL - AttributeError: '_provider_sets'

**Step 3: Add with_providers to CheckHub**

In `src/checkup/hub.py`, update the `__init__` and add `with_providers`:

Find and replace the `__init__` method:

```python
def __init__(self, config_path: Path | None = None) -> None:
    """Initialize CheckHub.

    Args:
        config_path: Optional path to YAML config file
    """
    self._metrics: list[type[Metric]] = []
    self._provider_sets: list[list[Provider]] = []
    self._config_path = config_path
```

Add this method after `with_metrics`:

```python
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
```

Also update the imports at the top of hub.py to include `Iterable`:

```python
from typing import TYPE_CHECKING, Any, Iterable
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_hub_with_providers.py -v`
Expected: PASS

---

## Task 4: Add Provider Validation

**Files:**
- Modify: `src/checkup/hub.py`
- Test: `tests/test_hub_validation.py`

**Step 1: Write failing tests for provider validation**

Create `tests/test_hub_validation.py`:

```python
"""Tests for provider validation in CheckHub."""

from typing import Any, ClassVar

import pytest

from checkup.hub import CheckHub
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context


class RequiredProvider(Provider):
    """Provider that metrics require."""

    name: ClassVar[str] = "required"

    def provide(self) -> dict[str, Any]:
        return {"data": "value"}


class OtherProvider(Provider):
    """Another provider."""

    name: ClassVar[str] = "other"

    def provide(self) -> dict[str, Any]:
        return {"other": "data"}


class MetricWithProvider(Metric):
    """Metric that requires a provider."""

    name: ClassVar[str] = "needs_provider"
    description: ClassVar[str] = "Needs RequiredProvider"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [RequiredProvider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1


class TestProviderValidation:
    """Tests for _validate_providers method."""

    def test_validation_passes_with_required_providers(self):
        """Test validation passes when all required providers present."""
        hub = CheckHub().with_metrics([MetricWithProvider])
        hub._validate_providers(
            metrics=[MetricWithProvider],
            provider_sets=[[RequiredProvider()]],
        )
        # No exception raised

    def test_validation_fails_with_missing_provider(self):
        """Test validation fails when required provider missing."""
        hub = CheckHub().with_metrics([MetricWithProvider])

        with pytest.raises(ValueError) as exc_info:
            hub._validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[[OtherProvider()]],
            )

        assert "required" in str(exc_info.value).lower()

    def test_validation_fails_with_empty_provider_set(self):
        """Test validation fails with empty provider set."""
        hub = CheckHub().with_metrics([MetricWithProvider])

        with pytest.raises(ValueError) as exc_info:
            hub._validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[[]],
            )

        assert "required" in str(exc_info.value).lower()

    def test_validation_checks_all_provider_sets(self):
        """Test validation checks each provider set independently."""
        hub = CheckHub().with_metrics([MetricWithProvider])

        with pytest.raises(ValueError) as exc_info:
            hub._validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[
                    [RequiredProvider()],  # OK
                    [OtherProvider()],  # Missing
                ],
            )

        assert "1" in str(exc_info.value)  # Provider set index

    def test_validation_passes_with_no_required_providers(self):
        """Test validation passes when metrics need no providers."""
        from conftest import DummyMetric

        hub = CheckHub().with_metrics([DummyMetric])
        hub._validate_providers(
            metrics=[DummyMetric],
            provider_sets=[[]],
        )
        # No exception raised
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_hub_validation.py -v`
Expected: FAIL - AttributeError: '_validate_providers'

**Step 3: Implement _validate_providers**

In `src/checkup/hub.py`, add this method after `_collect_providers`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_hub_validation.py -v`
Expected: PASS

---

## Task 5: Update Hub Execution Flow

**Files:**
- Modify: `src/checkup/hub.py`
- Test: `tests/test_hub_execution.py`

**Step 1: Write failing tests for new execution flow**

Create `tests/test_hub_execution.py`:

```python
"""Tests for CheckHub execution with instance-based providers."""

from typing import Any, ClassVar

from checkup.hub import CheckHub
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.providers.tags import TagProvider
from checkup.types import Context


class DataProvider(Provider):
    """Provider that supplies data."""

    name: ClassVar[str] = "data"

    def __init__(self, value: int = 100):
        self.value = value

    def provide(self) -> dict[str, Any]:
        return {"value": self.value}


class DataMetric(Metric):
    """Metric that uses DataProvider."""

    name: ClassVar[str] = "data_metric"
    description: ClassVar[str] = "Uses data provider"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DataProvider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context[DataProvider.name]["value"]


class TestHubExecution:
    """Tests for measure() with new provider system."""

    def test_measure_with_single_provider_set(self):
        """Test measuring with single provider set."""
        result = (
            CheckHub()
            .with_metrics([DataMetric])
            .with_providers([[DataProvider(value=42)]])
            .measure()
        )

        assert len(result.metrics) == 1
        assert result.metrics[0].value == 42

    def test_measure_with_multiple_provider_sets(self):
        """Test measuring across multiple provider sets."""
        result = (
            CheckHub()
            .with_metrics([DataMetric])
            .with_providers([
                [DataProvider(value=10)],
                [DataProvider(value=20)],
                [DataProvider(value=30)],
            ])
            .measure()
        )

        assert len(result.metrics) == 3
        values = {m.value for m in result.metrics}
        assert values == {10, 20, 30}

    def test_measure_with_tag_provider(self):
        """Test that TagProvider merges into metric tags."""
        result = (
            CheckHub()
            .with_metrics([DataMetric])
            .with_providers([
                [DataProvider(value=42), TagProvider(env="prod", team="data")],
            ])
            .measure()
        )

        metric = result.metrics[0]
        assert metric.tags["env"] == "prod"
        assert metric.tags["team"] == "data"

    def test_measure_validates_providers(self):
        """Test that measure() validates providers before running."""
        import pytest

        with pytest.raises(ValueError) as exc_info:
            CheckHub().with_metrics([DataMetric]).with_providers([[]]).measure()

        assert "data" in str(exc_info.value).lower()

    def test_measure_with_empty_provider_sets_and_no_requirements(self):
        """Test measuring without providers when none required."""
        from conftest import DummyMetric

        result = CheckHub().with_metrics([DummyMetric]).measure()

        assert len(result.metrics) == 1
        assert result.metrics[0].value == 42
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_hub_execution.py -v`
Expected: FAIL - measure() doesn't use _provider_sets

**Step 3: Update measure() and related methods**

Replace these methods in `src/checkup/hub.py`:

First, remove `with_contexts` method entirely.

Then remove `_collect_providers` method entirely.

Then replace `_execute_providers`:

```python
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
```

Replace `_measure_single_context` with `_measure_single_provider_set`:

```python
def _measure_single_provider_set(
    self,
    provider_set: list[Provider],
    execution_order: list[type[Metric]],
    direct_metrics: set[type[Metric]],
    metric_configs: dict,
) -> list[Metric]:
    """Calculate all metrics for a single provider set.

    Args:
        provider_set: List of provider instances
        execution_order: Topologically sorted metric classes
        direct_metrics: Set of directly requested metric classes
        metric_configs: Config dict for metrics

    Returns:
        List of calculated metrics with tags merged
    """
    context, tags = self._execute_providers(provider_set)

    calculated: dict[type[Metric], Metric] = {}
    result_metrics: list[Metric] = []

    for metric_cls in execution_order:
        config = metric_configs.get(metric_cls.name, {})
        metric = metric_cls(**config, is_direct=(metric_cls in direct_metrics))
        metric.tags.update(tags)
        metric.calculate(context, calculated)
        calculated[metric_cls] = metric
        result_metrics.append(metric)

    return result_metrics
```

Replace the `measure` method:

```python
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
    direct_metrics = set(self._metrics)

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
                direct_metrics=direct_metrics,
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

    return MeasurementResult(metrics=all_metrics, errors=all_errors)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_hub_execution.py -v`
Expected: PASS

---

## Task 6: Remove FilesystemProvider and Update Exports

**Files:**
- Delete: `src/checkup/providers/filesystem.py`
- Delete: `tests/test_filesystem_provider.py`
- Modify: `src/checkup/__init__.py`

**Step 1: Delete FilesystemProvider**

Delete the file `src/checkup/providers/filesystem.py`.

**Step 2: Delete FilesystemProvider tests**

Delete the file `tests/test_filesystem_provider.py`.

**Step 3: Update main __init__.py**

Replace `src/checkup/__init__.py`:

```python
"""Checkup - Extensible metrics calculation framework."""

from checkup.hub import CheckHub, MeasurementResult
from checkup.materializers import ConsoleMaterializer, CSVMaterializer, Materializer
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.providers.tags import TagProvider
from checkup.types import Context, ContextDict

__all__ = [
    "CheckHub",
    "MeasurementResult",
    "Metric",
    "Provider",
    "TagProvider",
    "Materializer",
    "ConsoleMaterializer",
    "CSVMaterializer",
    "Context",
    "ContextDict",
]


def main() -> None:
    """CLI entry point."""
    print("Checkup metrics framework")
    print("Import CheckHub to get started")
```

**Step 4: Run all core tests**

Run: `uv run pytest tests/ -v --ignore=tests/test_hub.py --ignore=tests/test_providers.py --ignore=tests/test_hub_providers.py --ignore=tests/test_integration.py --ignore=tests/test_metric.py`
Expected: Some tests may fail due to old API usage

---

## Task 7: Update Test Fixtures (conftest.py)

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Update conftest.py providers**

In `tests/conftest.py`, update all provider classes from classmethod to instance method:

Find `class DummyProvider(Provider):` and replace the entire class:

```python
class DummyProvider(Provider):
    """Test provider that adds dummy data to context."""

    name: ClassVar[str] = "dummy"

    def __init__(self, data: int = 100):
        self.data = data

    def provide(self) -> dict[str, Any]:
        return {"data": self.data}
```

Find `class IntegrationProvider(Provider):` and replace:

```python
class IntegrationProvider(Provider):
    """Provider that adds base_value to context."""

    name: ClassVar[str] = "integration"

    def __init__(self, base_value: int = 25):
        self.base_value = base_value

    def provide(self) -> dict[str, Any]:
        return {"base_value": self.base_value}
```

Find `class PathLengthProvider(Provider):` and replace:

```python
class PathLengthProvider(Provider):
    """Provider that returns path length."""

    name: ClassVar[str] = "path_length"

    def __init__(self, path: str = "/unknown"):
        self.path = path

    def provide(self) -> dict[str, Any]:
        return {"length": len(self.path)}
```

Remove the legacy function definitions:
- `def dummy_provider(context: Context) -> Context:`
- `def integration_provider(context: Context) -> Context:`
- `def path_length_provider(context: Context) -> Context:`

**Step 2: Run conftest import check**

Run: `uv run python -c "from tests.conftest import DummyProvider, IntegrationProvider, PathLengthProvider; print('OK')"`
Expected: OK

---

## Task 8: Update Remaining Core Tests

**Files:**
- Modify: `tests/test_hub.py`
- Modify: `tests/test_metric.py`
- Modify: `tests/test_integration.py`
- Delete: `tests/test_providers.py`
- Delete: `tests/test_hub_providers.py`

**Step 1: Update test_hub.py**

Replace tests that use `with_contexts` with `with_providers`. Key changes:

In `test_checkhub_measure_with_contexts`, rename to `test_checkhub_measure_with_providers`:

```python
def test_checkhub_measure_with_providers():
    """Test that providers are executed correctly."""
    from conftest import DummyProvider, ProviderDummyMetric

    result = (
        CheckHub()
        .with_metrics([ProviderDummyMetric])
        .with_providers([[DummyProvider()]])
        .measure()
    )

    assert result.metrics[0].value == 100  # Provider works
```

Delete `test_checkhub_with_contexts` test.

Update `test_checkhub_measure_single_context` - this test uses internal methods that changed, delete it.

Update `test_checkhub_measure_multiple_contexts` to use `with_providers`:

```python
def test_checkhub_measure_multiple_provider_sets():
    """Test measuring metrics across multiple provider sets."""
    from checkup.providers.tags import TagProvider

    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_providers([
            [TagProvider(path="/repo1")],
            [TagProvider(path="/repo2")],
            [TagProvider(path="/repo3")],
        ])
        .measure()
    )

    assert len(result.metrics) == 3
    paths = {m.tags["path"] for m in result.metrics}
    assert paths == {"/repo1", "/repo2", "/repo3"}
```

Update `test_checkhub_measure_parallel`:

```python
def test_checkhub_measure_parallel():
    """Test parallel execution with max_workers."""
    from checkup.providers.tags import TagProvider

    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_providers([[TagProvider(path=f"/repo{i}")] for i in range(10)])
        .measure(max_workers=4)
    )

    assert len(result.metrics) == 10
```

Update `test_checkhub_measure_with_failing_context` - delete this test (FailingMetric reads from context directly which won't work).

**Step 2: Update test_metric.py**

Tests that use provider functions need updating. Find tests using `DummyProvider.provide({})` and update:

```python
def test_dummy_provider_enriches_context():
    """Test DummyProvider adds data."""
    from conftest import DummyProvider

    provider = DummyProvider()
    result = provider.provide()
    assert result == {"data": 100}
```

**Step 3: Update test_integration.py**

Replace the entire file to use new API:

```python
"""Integration tests for full checkup pipeline."""

from checkup.hub import CheckHub
from checkup.materializers import ConsoleMaterializer

from conftest import (
    DummyMetric,
    IntegrationBaseMetric,
    IntegrationDerivedMetric,
    IntegrationProvider,
    PathLengthProvider,
    PathMetric,
)
from checkup.providers.tags import TagProvider


def test_full_pipeline():
    """Test complete pipeline from provider through metric calculation."""
    result = (
        CheckHub()
        .with_metrics([IntegrationBaseMetric])
        .with_providers([[IntegrationProvider()]])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 25


def test_full_pipeline_with_both_metrics():
    """Test pipeline with dependent metrics."""
    result = (
        CheckHub()
        .with_metrics([IntegrationDerivedMetric])
        .with_providers([[IntegrationProvider()]])
        .measure()
    )

    # Both base and derived metrics should be calculated
    assert len(result.metrics) == 2
    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["base_metric"].value == 25
    assert metrics_by_name["derived_metric"].value == 50  # 25 * 2


def test_multi_provider_set_pipeline():
    """Test pipeline across multiple provider sets."""
    result = (
        CheckHub()
        .with_metrics([PathMetric])
        .with_providers([
            [PathLengthProvider(path="/short"), TagProvider(name="short")],
            [PathLengthProvider(path="/much/longer/path"), TagProvider(name="long")],
        ])
        .measure()
    )

    assert len(result.metrics) == 2

    metrics_by_name = {m.tags["name"]: m for m in result.metrics}
    assert metrics_by_name["short"].value == 6  # len("/short")
    assert metrics_by_name["long"].value == 17  # len("/much/longer/path")
```

**Step 4: Delete obsolete test files**

Delete `tests/test_providers.py` (tested old function-based provider collection).
Delete `tests/test_hub_providers.py` (tested old classmethod-based execution).

**Step 5: Run all core tests**

Run: `uv run pytest tests/ -v`
Expected: PASS (may need additional fixes)

---

## Task 9: Update DbtManifestProvider

**Files:**
- Modify: `plugins/checkup-dbt/src/checkup_dbt/provider.py`

**Step 1: Update DbtManifestProvider to instance-based**

Replace `plugins/checkup-dbt/src/checkup_dbt/provider.py`:

```python
"""dbt manifest provider for checkup."""

import json
import logging
import os
from pathlib import Path
from typing import Any, ClassVar

from dbt.cli.main import dbtRunner
from dbt.contracts.graph.manifest import Manifest

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class DbtManifestProvider(Provider):
    """Provides dbt manifest from file or by parsing project.

    Supports two modes:
    1. manifest_path: Load from pre-generated manifest.json
    2. dbt_project_dir: Run dbt parse to generate manifest

    Example:
        # From file
        DbtManifestProvider(manifest_path="./target/manifest.json")

        # From project
        DbtManifestProvider(dbt_project_dir="./my_dbt_project")
    """

    name: ClassVar[str] = "dbt"

    def __init__(
        self,
        manifest_path: str | Path | None = None,
        dbt_project_dir: str | Path | None = None,
        profiles_dir: str | Path | None = None,
    ):
        """Initialize DbtManifestProvider.

        Args:
            manifest_path: Path to pre-generated manifest.json
            dbt_project_dir: Path to dbt project (runs dbt parse)
            profiles_dir: Optional profiles directory (defaults to project dir)

        Raises:
            ValueError: If neither manifest_path nor dbt_project_dir provided
        """
        if manifest_path is None and dbt_project_dir is None:
            raise ValueError(
                "Must provide either 'manifest_path' or 'dbt_project_dir'"
            )

        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.dbt_project_dir = Path(dbt_project_dir) if dbt_project_dir else None
        self.profiles_dir = Path(profiles_dir) if profiles_dir else None

    def provide(self) -> dict[str, Any]:
        """Load dbt manifest from file or by parsing project.

        Returns:
            Dict with 'manifest' key containing Manifest object
        """
        if self.manifest_path:
            return self._load_from_file()
        return self._parse_project()

    def _load_from_file(self) -> dict[str, Any]:
        """Load manifest from pre-generated file."""
        logger.info(f"Loading manifest from {self.manifest_path}")

        with open(self.manifest_path) as f:
            manifest_dict = json.load(f)

        manifest = Manifest.from_dict(manifest_dict)
        return {"manifest": manifest}

    def _parse_project(self) -> dict[str, Any]:
        """Parse dbt project to generate manifest."""
        logger.info(f"Parsing dbt project at {self.dbt_project_dir}")

        cwd = Path.cwd()

        try:
            common_args = ["--project-dir", str(self.dbt_project_dir)]

            profiles_dir = self.profiles_dir or self.dbt_project_dir
            common_args.extend(["--profiles-dir", str(profiles_dir)])

            logger.info("Running dbt deps...")
            deps_result = dbtRunner().invoke(["deps", *common_args])
            if not deps_result.success:
                raise RuntimeError(f"dbt deps failed: {deps_result.exception}")

            logger.info("Running dbt parse...")
            parse_result = dbtRunner().invoke(["parse", *common_args])
            if not parse_result.success:
                raise RuntimeError(f"dbt parse failed: {parse_result.exception}")

            manifest = parse_result.result
            return {"manifest": manifest}

        finally:
            os.chdir(cwd)
```

**Step 2: Verify provider imports**

Run: `cd plugins/checkup-dbt && uv run python -c "from checkup_dbt.provider import DbtManifestProvider; print('OK')"`
Expected: OK

---

## Task 10: Update dbt Plugin Tests

**Files:**
- Modify: `plugins/checkup-dbt/tests/test_provider.py`
- Modify: `plugins/checkup-dbt/tests/conftest.py` (if it has provider setup)

**Step 1: Update test_provider.py**

Replace `plugins/checkup-dbt/tests/test_provider.py`:

```python
from pathlib import Path

import pytest

from checkup.hub import CheckHub
from checkup.providers.tags import TagProvider
from checkup_dbt import DbtModelsMetric
from checkup_dbt.provider import DbtManifestProvider


def test_manifest_path_mode(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 3


def test_dbt_project_dir_mode(sample_dbt_project_dir: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([[
            DbtManifestProvider(
                dbt_project_dir=sample_dbt_project_dir,
                profiles_dir=sample_dbt_project_dir,
            )
        ]])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 3


def test_missing_args_raises_error():
    with pytest.raises(ValueError) as exc_info:
        DbtManifestProvider()

    assert "manifest_path" in str(exc_info.value) or "dbt_project_dir" in str(exc_info.value)


def test_multiple_projects(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([
            [DbtManifestProvider(manifest_path=sample_manifest_path), TagProvider(project="project_a")],
            [DbtManifestProvider(manifest_path=sample_manifest_path), TagProvider(project="project_b")],
        ])
        .measure()
    )

    assert len(result.metrics) == 2
    assert all(m.value == 3 for m in result.metrics)
    projects = {m.tags["project"] for m in result.metrics}
    assert projects == {"project_a", "project_b"}
```

**Step 2: Update other dbt test files**

Update all other test files in `plugins/checkup-dbt/tests/` to use the new API:
- `test_core_metrics.py`
- `test_output_metrics.py`
- `test_quality_metrics.py`
- `test_test_metrics.py`
- `test_all_metrics.py`

For each file, replace `.with_contexts([{"manifest_path": str(sample_manifest_path)}])` with `.with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])`.

Example for `test_core_metrics.py`:

```python
from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import (
    DbtColumnsMetric,
    DbtColumnsWithDescriptionMetric,
    DbtModelsMetric,
    DbtModelsWithDescriptionMetric,
    DbtTestsMetric,
)
from checkup_dbt.provider import DbtManifestProvider


def test_models_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert result.metrics[0].value == 3


# ... similar updates for other tests
```

**Step 3: Run dbt plugin tests**

Run: `cd plugins/checkup-dbt && uv run pytest tests/ -v`
Expected: PASS

---

## Task 11: Final Verification

**Step 1: Run all core tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 2: Run all dbt plugin tests**

Run: `cd plugins/checkup-dbt && uv run pytest tests/ -v`
Expected: All PASS

**Step 3: Verify clean imports**

Run: `uv run python -c "from checkup import CheckHub, Provider, TagProvider, Metric; print('Core imports OK')"`
Run: `cd plugins/checkup-dbt && uv run python -c "from checkup_dbt import DbtManifestProvider, DbtModelsMetric; print('Plugin imports OK')"`
Expected: Both OK
