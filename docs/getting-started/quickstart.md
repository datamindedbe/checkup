# Quick Start

This guide will help you get started with CheckUp by walking through a complete example.

## Creating Your First Metric

A metric is a class that calculates a value from context and returns a Measurement. Here's a simple example:

```python
from checkup import Metric, Measurement
from checkup.types import Context


class FileCountMetric(Metric):
    name = "file_count"
    description = "Number of files in the project"
    unit = "files"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Access data from context and calculate your metric
        files = context.get("files", [])
        return self.measurement(
            value=len(files),
            diagnostic=f"Found {len(files)} files"
        )
```

Every metric must:

1. Define `name`, `description`, and `unit` class attributes
2. Implement the `calculate()` method
3. Return a `Measurement` using `self.measurement(value=..., diagnostic=...)`

## Running Metrics with CheckHub

Use `CheckHub` to orchestrate metric calculation:

```python
from checkup import CheckHub, ConsoleMaterializer


# Create and run the pipeline
result = (
    CheckHub()
    .with_metrics([FileCountMetric()])
    .measure()
)

# Output results to console
result.materialize(
    ConsoleMaterializer(group_tag_1="domain", group_tag_2="project")
)
```

## Adding Context with Providers

Providers enrich the context with external data that metrics can use:

```python
from checkup import Provider
from typing import Any, ClassVar
from pathlib import Path


class FileProvider(Provider):
    name: ClassVar[str] = "files"

    def __init__(self, directory: Path):
        self.directory = directory

    def provide(self) -> dict[str, Any]:
        files = list(self.directory.glob("**/*"))
        return {"file_list": files, "root": self.directory}
```

Now update your metric to use the provider:

```python
class FileCountMetric(Metric):
    name = "file_count"
    description = "Number of files in the project"
    unit = "files"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [FileProvider]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Access provider data under its namespace
        files = context["files"]["file_list"]
        return self.measurement(value=len(files))
```

Run with providers:

```python
from pathlib import Path

result = (
    CheckHub()
    .with_metrics([FileCountMetric()])
    .with_providers([
        [FileProvider(Path("./src"))],
        [FileProvider(Path("./tests"))],
    ])
    .measure()
)
```

## Metric Dependencies

Metrics can depend on other metrics:

```python
class TotalLinesMetric(Metric):
    name = "total_lines"
    description = "Total lines of code"
    unit = "lines"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        # Count lines in all files
        return self.measurement(value=1000)  # simplified


class AverageLinesPerFileMetric(Metric):
    name = "avg_lines_per_file"
    description = "Average lines per file"
    unit = "lines/file"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [FileCountMetric, TotalLinesMetric]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        file_count = measurements[FileCountMetric].value
        total_lines = measurements[TotalLinesMetric].value

        if file_count > 0:
            return self.measurement(value=total_lines / file_count)
        else:
            return self.measurement(value=0, diagnostic="No files found")
```

CheckUp automatically resolves dependencies and calculates metrics in the correct order.

## Output Formats

### Console Output

```python
from checkup import ConsoleMaterializer

result.materialize(
    ConsoleMaterializer(group_tag_1="domain", group_tag_2="project")
)
```

### CSV Export

```python
from checkup import CSVMaterializer
from pathlib import Path

result.materialize(
    CSVMaterializer(output_path=Path("metrics.csv"))
)
```

### HTML Report

```python
from checkup import HTMLMaterializer
from pathlib import Path

result.materialize(
    HTMLMaterializer(
        output_path=Path("report.html"),
        group_tag_1="domain",
        group_tag_2="project"
    )
)
```

## Using Configuration Files

Create a YAML configuration file for metric settings:

```yaml
# checkup.yaml
metrics:
  file_count:
    threshold: 100
  total_lines:
    max_allowed: 10000
```

Load the configuration:

```python
from pathlib import Path

result = (
    CheckHub(config_path=Path("checkup.yaml"))
    .with_metrics([FileCountMetric(), TotalLinesMetric()])
    .measure()
)
```

## Next Steps

- Learn more about [Metrics](../concepts/metrics.md)
- Explore [Providers](../concepts/providers.md)
- Check out available [Plugins](../plugins/overview.md)
