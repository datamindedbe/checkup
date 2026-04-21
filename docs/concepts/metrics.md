# Metrics

Metrics are the core building blocks of CheckUp. They calculate values from context data and can depend on other metrics.

## Defining a Metric

Create a metric by subclassing the `Metric` base class:

```python
from checkup import Metric, Measurement
from checkup.types import Context


class MyMetric(Metric):
    # Required class attributes
    name = "my_metric"
    description = "Description of what this metric measures"
    unit = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Your calculation logic here
        return self.measurement(value=42, diagnostic="Additional information")
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

Use `self.measurement()` to create a `Measurement` with the metric's metadata pre-filled:

```python
return self.measurement(value=42, diagnostic="Explanation", tags={"key": "value"})
```

## The Calculate Method

The `calculate` method is where you implement your metric logic:

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
    return self.measurement(value=computed_value, diagnostic="Explanation of result")
```

## Dependencies

Metrics can depend on other metrics. The framework ensures dependencies are calculated first:

```python
class BaseMetric(Metric):
    name = "base_metric"
    description = "A base metric"
    unit = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        return self.measurement(value=100)


class DerivedMetric(Metric):
    name = "derived_metric"
    description = "Depends on base metric"
    unit = "percent"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BaseMetric]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        base_value = measurements[BaseMetric].value
        return self.measurement(value=base_value * 0.5)
```

## Providers

Metrics can declare which providers they need:

```python
from checkup import Provider


class MyDataProvider(Provider):
    name = "my_data"
    # ...


class MyMetric(Metric):
    name = "my_metric"
    description = "Uses my_data provider"
    unit = "items"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [MyDataProvider]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Access provider data under its namespace
        data = context["my_data"]
        return self.measurement(value=len(data.get("items", [])))
```

## Executor Types

Metrics can specify how they should be executed:

```python
from checkup import ExecutorType


class IOBoundMetric(Metric):
    name = "io_metric"
    executor = ExecutorType.THREAD  # Default, for I/O-bound operations


class CPUBoundMetric(Metric):
    name = "cpu_metric"
    executor = ExecutorType.PROCESS  # For CPU-intensive calculations


class AsyncMetric(Metric):
    name = "async_metric"
    executor = ExecutorType.ASYNCIO  # For async I/O operations
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
    name = "tagged_metric"
    description = "A metric with tags"
    unit = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        return self.measurement(
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
from checkup import Metric, Provider, ExecutorType, Measurement
from checkup.types import Context


class CodeCoverageMetric(Metric):
    name = "code_coverage"
    description = "Percentage of code covered by tests"
    unit = "percent"
    executor = ExecutorType.THREAD

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [CoverageReportProvider]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        coverage_data = context.get("coverage", {})

        if not coverage_data:
            return self.measurement(value=None, diagnostic="No coverage data available")

        total_lines = coverage_data.get("total_lines", 0)
        covered_lines = coverage_data.get("covered_lines", 0)

        if total_lines > 0:
            value = round((covered_lines / total_lines) * 100, 2)
            diagnostic = f"{covered_lines}/{total_lines} lines covered"
        else:
            value = 0
            diagnostic = "No lines to cover"

        return self.measurement(
            value=value,
            diagnostic=diagnostic,
            tags={"project": coverage_data.get("project_name", "unknown")}
        )
```
