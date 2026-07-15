# CheckUp

![CheckUp](images/banner.png)

**Computational governance framework for measuring data product health.**

CheckUp calculates metrics from context data, so teams can track the health of their data products.

## Key Features

- **Metrics** - Calculate values from context with dependency management
- **Providers** - Functions that enrich context (shared across metrics)
- **Materializers** - Output formats (Console, HTML, CSV, and more)
- **Plugins** - Extensible architecture with built-in plugins for Git, dbt, Python, and Conveyor

## Quick Example

```python
from checkup import CheckHub, ConsoleMaterializer, Metric, Measurement
from checkup.types import Context


class SimpleMetric(Metric):
    name: str = "example_metric"
    description: str = "A simple example metric"
    unit: str = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        return self.measure(value=42, diagnostic="Calculated successfully")


# Run the metric and output to console
if __name__ == "__main__":
    (
        CheckHub()
        .with_metrics([SimpleMetric()])
        .measure()
        .materialize(ConsoleMaterializer(group_tag_1="domain", group_tag_2="project"))
    )
```

CheckUp runs metrics in a process pool, so scripts need the `if __name__ == "__main__":`
guard on platforms that spawn subprocesses, such as macOS and Windows.

## Installation

```bash
uv add checkup
```

## Getting Started

Start with the [Installation Guide](getting-started/installation.md), then the [Quick Start](getting-started/quickstart.md).

## Architecture

CheckUp uses a fluent API design centered around the `CheckHub` class:

```
CheckHub()
    .with_metrics([...])      # Register metrics to calculate
    .with_providers([...])    # Register provider sets for context
    .measure()                # Execute the pipeline
    .materialize(...)         # Output results
```

The framework automatically:

- Resolves metric dependencies using topological sorting
- Executes providers to enrich context
- Calculates metrics in parallel using process pools
- Handles errors gracefully with detailed reporting
