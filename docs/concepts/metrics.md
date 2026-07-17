# Metrics

Metrics are the core building blocks of CheckUp. They calculate values from context data and can depend on other metrics.

## Defining a Metric

Create a metric by subclassing the `Metric` base class:

```python
from checkup import Metric, Measurement
from checkup.types import Context


class MyMetric(Metric):
    # Required class attributes
    name: str = "my_metric"
    description: str = "Description of what this metric measures"
    unit: str = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Your calculation logic here
        return self.measure(value=42, diagnostic="Additional information")
```

## Required Attributes

Every metric must define these class attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Unique identifier for the metric |
| `description` | `str` | Human-readable description |
| `unit` | `str` | Unit of measurement (e.g., "count", "percent", "ms") |

## The Measurement Class

The `calculate` method returns a `Measurement` object containing:

| Attribute | Type | Description |
|-----------|------|-------------|
| `metric_name` | `str` | Name of the metric (set automatically) |
| `metric_description` | `str` | Description of the metric (set automatically) |
| `metric_unit` | `str` | Unit of measurement (set automatically) |
| `value` | `Any` | The calculated metric value |
| `diagnostic` | `str` | Additional diagnostic information |
| `tags` | `dict` | Key-value pairs for grouping/filtering |

Use `self.measure()` to create a `Measurement` with the metric's metadata pre-filled:

```python
return self.measure(value=42, diagnostic="Explanation", tags={"key": "value"})
```

## The Calculate Method

The `calculate` method holds your metric logic:

```python
def calculate(self, context: Context, measurements: dict) -> Measurement:
    # context: Dict containing provider data under namespaces
    # measurements: Dict mapping metric classes to their Measurement results

    # Access provider data
    git_data = context.get("git", {})

    # Access dependency metrics
    if SomeOtherMetric in measurements:
        other_value = measurements[SomeOtherMetric].value

    # Return the result
    return self.measure(value=computed_value, diagnostic="Explanation of result")
```

## Dependencies

Metrics can depend on other metrics. The framework ensures dependencies are calculated first:

```python
class BaseMetric(Metric):
    name: str = "base_metric"
    description: str = "A base metric"
    unit: str = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        return self.measure(value=100)


class DerivedMetric(Metric):
    name: str = "derived_metric"
    description: str = "Depends on base metric"
    unit: str = "percent"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BaseMetric]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        base_value = measurements[BaseMetric].value
        return self.measure(value=base_value * 0.5)
```

## Providers

Metrics can declare which providers they need:

```python
from checkup import Provider


class MyDataProvider(Provider):
    name = "my_data"
    # ...


class MyMetric(Metric):
    name: str = "my_metric"
    description: str = "Uses my_data provider"
    unit: str = "items"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [MyDataProvider]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Access provider data under its namespace
        data = context["my_data"]
        return self.measure(value=len(data.get("items", [])))
```

## Executor Types

Metrics can specify how they should be executed:

```python
from typing import ClassVar

from checkup import ExecutorType


class IOBoundMetric(Metric):
    name: str = "io_metric"
    executor: ClassVar[ExecutorType] = ExecutorType.THREAD  # Default, for I/O-bound operations


class CPUBoundMetric(Metric):
    name: str = "cpu_metric"
    executor: ClassVar[ExecutorType] = ExecutorType.PROCESS  # For CPU-intensive calculations


class AsyncMetric(Metric):
    name: str = "async_metric"
    executor: ClassVar[ExecutorType] = ExecutorType.ASYNCIO  # For async I/O operations
```

| Executor | Best For | Notes |
|----------|----------|-------|
| `THREAD` | I/O-bound operations | Default executor |
| `PROCESS` | CPU-intensive calculations | Requires picklable data |
| `ASYNCIO` | Async I/O operations | For async-native code |

## Tags

Tags allow grouping and filtering metrics. Tags can be set when creating the measurement:

```python
class TaggedMetric(Metric):
    name: str = "tagged_metric"
    description: str = "A metric with tags"
    unit: str = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        return self.measure(
            value=42,
            tags={"domain": "data-platform", "project": "analytics"}
        )
```

Tags are also merged from `TagProvider` instances in the provider set.

Tags are used by materializers for grouping output:

```python
result.materialize(
    ConsoleMaterializer(group_tag_1="domain", group_tag_2="project")
)
```

## Best Practices

1. **Keep metrics focused**: Each metric should measure one specific thing
2. **Use meaningful names**: Names should clearly indicate what is being measured
3. **Provide diagnostics**: Include helpful information in the diagnostic field
4. **Declare dependencies explicitly**: Always use `depends_on()` for metric dependencies
5. **Handle missing data gracefully**: Check for missing context data and provide sensible defaults
6. **Use appropriate executors**: Choose the right executor for your metric's workload

## Example: Complete Metric

```python
from typing import ClassVar

from checkup import Metric, Provider, ExecutorType, Measurement
from checkup.types import Context


class CodeCoverageMetric(Metric):
    name: str = "code_coverage"
    description: str = "Percentage of code covered by tests"
    unit: str = "percent"
    executor: ClassVar[ExecutorType] = ExecutorType.THREAD

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [CoverageReportProvider]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        coverage_data = context.get("coverage", {})

        if not coverage_data:
            return self.measure(value=None, diagnostic="No coverage data available")

        total_lines = coverage_data.get("total_lines", 0)
        covered_lines = coverage_data.get("covered_lines", 0)

        if total_lines > 0:
            value = round((covered_lines / total_lines) * 100, 2)
            diagnostic = f"{covered_lines}/{total_lines} lines covered"
        else:
            value = 0
            diagnostic = "No lines to cover"

        return self.measure(
            value=value,
            diagnostic=diagnostic,
            tags={"project": coverage_data.get("project_name", "unknown")}
        )
```
