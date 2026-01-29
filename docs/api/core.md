# Core API Reference

This page documents the core CheckUp API.

## CheckHub

The main orchestrator class for running metrics.

```python
from checkup import CheckHub
```

### Constructor

```python
CheckHub(config_path: Path | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_path` | `Path \| None` | `None` | Path to YAML configuration file |

### Methods

#### with_metrics

```python
def with_metrics(self, metrics: Iterable[type[Metric]]) -> CheckHub
```

Register metrics to calculate.

**Parameters:**
- `metrics`: Iterable of metric classes

**Returns:** Self for method chaining

#### with_providers

```python
def with_providers(self, provider_sets: Iterable[Iterable[Provider]]) -> CheckHub
```

Register provider sets for context enrichment.

**Parameters:**
- `provider_sets`: Iterable of provider iterables. Each inner iterable is a set of providers for one measurement run.

**Returns:** Self for method chaining

#### measure

```python
def measure(self, max_workers: int | None = None) -> MeasurementResult
```

Execute the measurement pipeline.

**Parameters:**
- `max_workers`: Maximum parallel workers. `None` uses all CPUs.

**Returns:** `MeasurementResult` containing calculated metrics

**Raises:**
- `DuplicateMetricNameError`: If multiple metrics have the same name

---

## MeasurementResult

Result container from `CheckHub.measure()`.

```python
from checkup import MeasurementResult
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `metrics` | `list[Metric]` | All calculated metrics |
| `direct_metric_names` | `set[str]` | Names of directly requested metrics |
| `errors` | `list[tuple[list[Provider], Exception]]` | Provider failures |

### Methods

#### materialize

```python
def materialize(self, materializer: Materializer) -> None
```

Output results using a materializer.

---

## Metric

Abstract base class for all metrics.

```python
from checkup import Metric
```

### Class Attributes (Required)

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Unique metric identifier |
| `description` | `str` | Human-readable description |
| `unit` | `str` | Unit of measurement |

### Class Attributes (Optional)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `executor` | `ExecutorType` | `THREAD` | Executor type for calculation |

### Instance Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `value` | `Any` | Calculated value |
| `diagnostic` | `str` | Additional information |
| `tags` | `dict` | Key-value pairs for grouping |

### Abstract Methods

#### calculate

```python
@abstractmethod
def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None
```

Calculate the metric value. Must set `self.value`.

### Class Methods

#### depends_on

```python
@classmethod
def depends_on(cls) -> list[type[Metric]]
```

Return list of metric classes this metric depends on.

**Returns:** List of metric classes (empty by default)

#### providers

```python
@classmethod
def providers(cls) -> list[type[Provider]]
```

Return list of provider classes required by this metric.

**Returns:** List of provider classes (empty by default)

---

## ExecutorType

Enum for metric execution strategies.

```python
from checkup import ExecutorType
```

| Value | Description |
|-------|-------------|
| `THREAD` | ThreadPoolExecutor (default) - I/O-bound operations |
| `PROCESS` | ProcessPoolExecutor - CPU-intensive operations |
| `ASYNCIO` | asyncio event loop - async I/O operations |

---

## Provider

Abstract base class for context providers.

```python
from checkup import Provider
```

### Class Attributes (Required)

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Namespace for provider data |

### Abstract Methods

#### provide

```python
@abstractmethod
def provide(self) -> dict[str, Any]
```

Generate data to add to context under this provider's namespace.

**Returns:** Dict of data

### Methods

#### is_tag_provider

```python
def is_tag_provider(self) -> bool
```

Return `True` if this provider supplies tags instead of context data.

**Returns:** `False` by default

---

## TagProvider

Base class for providers that add tags to metrics.

```python
from checkup import TagProvider
```

Extends `Provider` with `is_tag_provider()` returning `True`.

---

## Materializers

### Materializer (Base)

```python
from checkup import Materializer
```

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_indirect` | `bool` | `False` | Include dependency metrics |

### ConsoleMaterializer

```python
from checkup import ConsoleMaterializer

ConsoleMaterializer(
    group_tag_1: str,
    group_tag_2: str,
    include_indirect: bool = False
)
```

### CSVMaterializer

```python
from checkup import CSVMaterializer

CSVMaterializer(
    output_path: Path,
    include_indirect: bool = False
)
```

### HTMLMaterializer

```python
from checkup import HTMLMaterializer

HTMLMaterializer(
    output_path: Path,
    group_tag_1: str,
    group_tag_2: str,
    include_indirect: bool = False
)
```

---

## Exceptions

```python
from checkup import (
    ProviderError,
    MetricPicklingError,
    DuplicateMetricNameError,
)
```

| Exception | Description |
|-----------|-------------|
| `ProviderError` | Raised when a provider fails |
| `MetricPicklingError` | Raised when a metric cannot be pickled |
| `DuplicateMetricNameError` | Raised when metrics have duplicate names |

---

## Types

### Context

```python
from checkup.types import Context
```

Type alias for the context dictionary: `dict[str, Any]`
