# Metrics

Metrics are the core building blocks of CheckUp. They calculate values from context data and can depend on other metrics.

## Defining a Metric

Create a metric by subclassing the `Metric` base class:

```python
from checkup import Metric
from checkup.types import Context


class MyMetric(Metric):
    # Required class attributes
    name = "my_metric"
    description = "Description of what this metric measures"
    unit = "count"

    def calculate(self, context: Context, metrics: dict) -> None:
        # Your calculation logic here
        self.value = 42
        self.diagnostic = "Additional information"
```

## Required Attributes

Every metric must define these class attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Unique identifier for the metric |
| `description` | `str` | Human-readable description |
| `unit` | `str` | Unit of measurement (e.g., "count", "percent", "ms") |

## Instance Attributes

After calculation, metrics have these instance attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `value` | `Any` | The calculated metric value |
| `diagnostic` | `str` | Additional diagnostic information |
| `tags` | `dict` | Key-value pairs for grouping/filtering |

## The Calculate Method

The `calculate` method is where you implement your metric logic:

```python
def calculate(self, context: Context, metrics: dict) -> None:
    # context: Dict containing provider data under namespaces
    # metrics: Dict mapping metric classes to calculated instances

    # Access provider data
    git_data = context.get("git", {})

    # Access dependency metrics
    if SomeOtherMetric in metrics:
        other_value = metrics[SomeOtherMetric].value

    # Set the result
    self.value = computed_value
    self.diagnostic = "Explanation of result"
```

## Dependencies

Metrics can depend on other metrics. The framework ensures dependencies are calculated first:

```python
class BaseMetric(Metric):
    name = "base_metric"
    description = "A base metric"
    unit = "count"

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 100


class DerivedMetric(Metric):
    name = "derived_metric"
    description = "Depends on base metric"
    unit = "percent"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BaseMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        base_value = metrics[BaseMetric].value
        self.value = base_value * 0.5
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

    def calculate(self, context: Context, metrics: dict) -> None:
        # Access provider data under its namespace
        data = context["my_data"]
        self.value = len(data.get("items", []))
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

Tags allow grouping and filtering metrics:

```python
class TaggedMetric(Metric):
    name = "tagged_metric"
    description = "A metric with tags"
    unit = "count"

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 42
        # Tags can be set during calculation
        self.tags["domain"] = "data-platform"
        self.tags["project"] = "analytics"
```

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
from checkup import Metric, Provider, ExecutorType
from checkup.types import Context


class CodeCoverageMetric(Metric):
    name = "code_coverage"
    description = "Percentage of code covered by tests"
    unit = "percent"
    executor = ExecutorType.THREAD

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [CoverageReportProvider]

    def calculate(self, context: Context, metrics: dict) -> None:
        coverage_data = context.get("coverage", {})

        if not coverage_data:
            self.value = None
            self.diagnostic = "No coverage data available"
            return

        total_lines = coverage_data.get("total_lines", 0)
        covered_lines = coverage_data.get("covered_lines", 0)

        if total_lines > 0:
            self.value = round((covered_lines / total_lines) * 100, 2)
            self.diagnostic = f"{covered_lines}/{total_lines} lines covered"
        else:
            self.value = 0
            self.diagnostic = "No lines to cover"

        self.tags["project"] = coverage_data.get("project_name", "unknown")
```
