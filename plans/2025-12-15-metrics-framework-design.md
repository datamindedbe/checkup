# Metrics Framework Design

**Date:** 2025-12-15
**Status:** Approved

## Overview

A framework for calculating metrics based on context. Metrics are extensible via an ABC-based plugin system. The framework handles dependency resolution, context enrichment via providers, metric calculation with caching, and result materialization to various formats.

## Core Concepts

### Context

**Context** is a dictionary containing data that metrics need for calculation. There are two types:

1. **Provider Context** - Configuration read from environment variables (credentials, hostnames, file paths)
2. **Metric-Specific Context** - Data computed by providers and shared across metrics

```python
Context = dict[str, Any]
```

### Metrics

Metrics are Pydantic models that:
- Calculate a value from context and other metrics
- Can depend on other metrics (explicit dependencies)
- Can declare providers to enrich context
- Support bounds/thresholds for validation (loaded from YAML)
- Are comparable via `__eq__` and `__lt__` for ordinal types

### Providers

Providers are functions that enrich the metric-specific context. They:
- Read configuration from environment variables
- Are shared across metrics (deduplicated by function identity)
- Execute independently (no dependencies between providers)
- Return an enriched context dictionary

### Materializers

Materializers format and output metric results to different formats (HTML, CSV, etc.).

## High-Level Architecture

The framework operates in three phases:

### 1. Setup Phase
- User creates `CheckHub` and registers metrics via `.with_metrics(metrics)`
- Metrics are classes (not instances) that implement the `Metric` ABC

### 2. Measurement Phase (`.measure()`)

**Step 2a: Load Configuration**
- Load metric bounds from YAML config
- Parse into metric-specific configs (keyed by metric name)

**Step 2b: Provider Execution**
- Collect all provider functions from all metrics
- Deduplicate providers by function identity
- Execute all providers independently to enrich metric-specific context

**Step 2c: Metric Instantiation & Calculation**
- Build dependency graph from `depends_on()` declarations
- Topological sort to determine calculation order
- For each metric in order:
  - Instantiate metric with bounds from YAML config: `metric = MetricClass(**config)`
  - Call `metric.calculate(context, cached_metrics)` to set `metric.value`
  - Cache the metric instance for dependent metrics

### 3. Materialization Phase (`.materialize(materializer)`)
- Pass calculated metrics to materializer
- Materializer formats and outputs results

## Detailed Design

### Metric ABC

```python
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

Context = dict[str, Any]

class Metric(ABC, BaseModel):
    # Core attributes
    name: str
    description: str
    unit: str  # e.g., "version", "percentage", "count"
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
        """Return list of metric classes this metric depends on."""
        return []

    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        """Return list of provider functions to enrich context."""
        return []
```

### Example Metric

```python
class PythonVersionMetric(Metric):
    name: str = "python_version"
    description: str = "Python version check"
    unit: str = "version"

    # Metric-specific config (from YAML)
    min: Optional[str] = None
    max: Optional[str] = None

    def calculate(self, context: Context, metrics: dict) -> None:
        import sys
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.value = version

        # Validate against bounds
        if self.min and version < self.min:
            raise ValueError(f"Python version {version} below minimum {self.min}")
        if self.max and version > self.max:
            raise ValueError(f"Python version {version} above maximum {self.max}")
```

### Providers

```python
# Shared provider function
def load_dbt_manifest(context: Context) -> Context:
    """Load dbt manifest from project path."""
    project_path = os.getenv('DBT_PROJECT_PATH')
    if not project_path:
        raise ValueError("DBT_PROJECT_PATH environment variable not set")

    manifest_path = Path(project_path) / "target" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())

    return {**context, 'dbt_manifest': manifest}

class DbtModelCountMetric(Metric):
    name: str = "dbt_model_count"
    description: str = "Number of dbt models"
    unit: str = "count"

    min: Optional[int] = None
    max: Optional[int] = None

    @classmethod
    def providers(cls):
        return [load_dbt_manifest]  # Reusable provider

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context['dbt_manifest']
        model_count = len([n for n in manifest['nodes'].values() if n['resource_type'] == 'model'])
        self.value = model_count

        if self.min and model_count < self.min:
            raise ValueError(f"Model count {model_count} below minimum {self.min}")
```

### CheckHub API

```python
class CheckHub:
    def __init__(self):
        self._metrics: list[type[Metric]] = []

    def with_metrics(self, metrics: Iterable[type[Metric]]) -> 'CheckHub':
        """Register metrics to calculate."""
        self._metrics.extend(metrics)
        return self

    def measure(self) -> 'MeasurementResult':
        """Execute providers and calculate all metrics.

        Returns:
            MeasurementResult containing calculated metrics
        """
        # 1. Load YAML config -> metric_configs: dict[str, dict]
        # 2. Collect and deduplicate providers
        # 3. Execute providers to build context
        # 4. Build dependency graph
        # 5. Topological sort
        # 6. For each metric in order:
        #    - Instantiate: metric = MetricClass(**metric_configs.get(name, {}))
        #    - Calculate: metric.calculate(context, cached_metrics)
        #    - Cache: cached_metrics[MetricClass] = metric
        # 7. Return MeasurementResult
        return MeasurementResult(metrics=calculated_metrics)

class MeasurementResult(BaseModel):
    metrics: list[Metric]

    def materialize(self, materializer: 'Materializer') -> None:
        """Output results using materializer."""
        materializer.materialize(self.metrics)
```

### Usage Example

```python
from checkup import CheckHub, HtmlMaterializer

result = (
    CheckHub()
    .with_metrics([
        PythonVersionMetric,
        TestCoverageMetric,
        DbtModelCountMetric,
    ])
    .measure()
    .materialize(HtmlMaterializer(output_path="report.html"))
)
```

### YAML Configuration

```yaml
# checkup.yaml - contains metric bounds for validation
metrics:
  python_version:
    min: "3.11.0"
    max: "3.12.99"

  test_coverage:
    min: 80.0
    max: 100.0

  dbt_model_count:
    min: 10
```

This config is loaded and used when instantiating metrics:
```python
metric_configs = {
    'python_version': {'min': '3.11.0', 'max': '3.12.99'},
    'test_coverage': {'min': 80.0, 'max': 100.0},
    'dbt_model_count': {'min': 10},
}

# Framework instantiates:
metric = PythonVersionMetric(**metric_configs.get('python_version', {}))
```

### Materializers

```python
class Materializer(ABC, BaseModel):
    @abstractmethod
    def materialize(self, metrics: list[Metric]) -> None:
        """Format and output metrics."""
        pass

class HtmlMaterializer(Materializer):
    output_path: str

    def materialize(self, metrics: list[Metric]) -> None:
        html = self._generate_html(metrics)
        Path(self.output_path).write_text(html)

    def _generate_html(self, metrics: list[Metric]) -> str:
        # Generate HTML report
        pass

class CsvMaterializer(Materializer):
    output_path: str

    def materialize(self, metrics: list[Metric]) -> None:
        # Generate CSV output
        pass
```

## Dependency Resolution

### Building the Graph

1. For each metric class, call `metric_cls.depends_on()` to get dependencies
2. Build directed graph: `{metric_class: [dependency_classes]}`
3. Detect cycles using DFS - raise error if found
4. Topological sort to get calculation order

### Calculation Order

1. Metrics with no dependencies calculate first
2. Once a metric calculates, cache its instance: `cache[MetricClass] = instance`
3. Dependent metrics calculate next, receiving cached instances via `metrics` parameter

### Caching Strategy

- **Cache scope:** Single `measure()` call only
- **Cache key:** Metric class (type)
- **Cache value:** Calculated metric instance
- **Purpose:** Avoid recalculating metrics when multiple metrics depend on the same base metric

## Error Handling

### Provider Failures
- If a provider raises an exception, fail fast with clear error message
- Show which provider failed and the underlying exception

### Metric Calculation Failures
- If a metric's `calculate()` raises an exception, catch and report
- Decision: Fail fast or continue calculating other metrics (TBD during implementation)

### Missing Dependencies
- Detect missing environment variables in providers - raise clear error
- Detect cyclic dependencies during graph building - raise error with cycle path

### Validation Failures
- When a metric value violates bounds, raise `ValueError` in `calculate()`
- Materializers can catch these and show pass/fail status

## Testing Strategy (TDD)

### Dummy Metrics for Testing

```python
class DummyMetric(Metric):
    """Simple test metric with no dependencies."""
    name: str = "dummy"
    description: str = "Test metric"
    unit: str = "count"

    expected_value: int = 42  # Config from YAML

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 42

class DependentDummyMetric(Metric):
    """Test metric that depends on DummyMetric."""
    name: str = "dependent_dummy"
    description: str = "Depends on dummy"
    unit: str = "count"

    @classmethod
    def depends_on(cls):
        return [DummyMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[DummyMetric].value * 2

class ProviderDummyMetric(Metric):
    """Test metric with a provider."""
    name: str = "provider_dummy"
    description: str = "Uses provider"
    unit: str = "count"

    @classmethod
    def providers(cls):
        return [dummy_provider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context['dummy_data']

def dummy_provider(context: Context) -> Context:
    """Test provider that adds dummy data."""
    return {**context, 'dummy_data': 100}
```

### Test Coverage

- Dependency graph building and topological sort
- Cycle detection
- Provider deduplication
- Metric instantiation with config
- Calculation order
- Caching
- Full pipeline integration test

## Project Structure

```
checkup/
├── src/checkup/
│   ├── __init__.py           # Export CheckHub, Metric, Materializer
│   ├── metric.py             # Metric ABC
│   ├── hub.py                # CheckHub implementation
│   ├── materializers.py      # Materializer ABC + built-ins
│   ├── graph.py              # Dependency graph & topological sort
│   ├── providers.py          # Provider utilities
│   └── config.py             # YAML config loading
├── tests/
│   ├── test_hub.py           # CheckHub tests
│   ├── test_graph.py         # Dependency resolution tests
│   ├── test_metrics.py       # DummyMetric tests
│   └── fixtures/
│       └── checkup.yaml      # Test config
├── pyproject.toml
└── README.md
```

## Implementation Order (TDD)

1. **Metric ABC + DummyMetric**
   - Define `Metric` ABC with Pydantic
   - Create `DummyMetric` for testing
   - Write tests for metric instantiation

2. **Dependency Graph**
   - Implement graph building from `depends_on()`
   - Topological sort algorithm
   - Cycle detection
   - Tests with `DependentDummyMetric`

3. **Provider System**
   - Provider collection from metrics
   - Deduplication by function identity
   - Execution and context enrichment
   - Tests with `ProviderDummyMetric`

4. **CheckHub.measure()**
   - Integrate providers, graph, and calculation
   - Metric instantiation with config
   - Caching
   - Integration tests

5. **Materializers**
   - `Materializer` ABC
   - `HtmlMaterializer` and `CsvMaterializer`
   - Tests for output generation

6. **YAML Config Loading**
   - Parse YAML file
   - Extract metric configs
   - Tests with fixtures

## Design Decisions

### ABC vs Protocol
**Decision:** Use ABC for strict contracts and explicit inheritance.
**Rationale:** Better IDE support, clearer interfaces, easier to enforce contracts in a framework.

### Explicit vs Implicit Dependencies
**Decision:** Explicit dependencies via `depends_on()`.
**Rationale:** Clear dependency graph, easier to debug, no inference needed.

### Provider Design
**Decision:** Providers return context enricher functions, deduplicated by identity.
**Rationale:** Avoids duplicate work, allows sharing across metrics, simple to reason about.

### Metric Dependencies vs Providers
**Decision:** Keep them separate - dependencies are about metric values, providers are about context.
**Rationale:** Clean separation of concerns, independent execution of providers.

### Comparison Strategy
**Decision:** Use Python's comparison protocol (`__eq__`, `__lt__`).
**Rationale:** Pythonic, works with built-in types, easy to extend for custom types like SemanticVersion.

### Caching Strategy
**Decision:** Cache within a single `measure()` run only.
**Rationale:** Simple, no cache invalidation complexity, handles the main use case.

### YAML Contents
**Decision:** YAML contains only metric bounds/thresholds.
**Rationale:** Keep metric selection and dependencies in Python where we have types. Config is for values only.

### Provider Context Source
**Decision:** Providers read from environment variables.
**Rationale:** Standard practice for credentials/config, simple, works well with deployment tools.

### Instance-Based Metrics
**Decision:** Metrics are instances (not classmethods), config passed to constructor.
**Rationale:** Cleaner design, Pydantic validation of config, better encapsulation.

## Future Considerations

- **Metric bundles:** Logical grouping of related metrics (deferred - YAGNI)
- **Temporal comparison:** Compare metrics over time (deferred - focus on validation first)
- **Cross-context comparison:** Compare metrics across different contexts (deferred)
- **Provider dependencies:** Allow providers to depend on other providers (not needed - keep simple)
- **Persistent caching:** Cache across runs (not needed - adds complexity)
- **Async providers:** For I/O-heavy operations (evaluate if performance becomes an issue)
