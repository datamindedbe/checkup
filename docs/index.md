# CheckUp

![CheckUp](images/horseshoe.png){ width="200" }

**Computational governance framework for measuring data product health.**

CheckUp is an extensible Python framework designed to calculate metrics from context data, enabling teams to measure and monitor the health of their data products.

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
    name = "example_metric"
    description = "A simple example metric"
    unit = "count"

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        return self.measure(value=42, diagnostic="Calculated successfully")


# Run the metric and output to console
(
    CheckHub()
    .with_metrics([SimpleMetric()])
    .measure()
    .materialize(ConsoleMaterializer(group_tag_1="domain", group_tag_2="project"))
)
```

## Installation

```bash
pip install checkup
```

## Getting Started

Ready to dive in? Check out the [Installation Guide](getting-started/installation.md) and [Quick Start](getting-started/quickstart.md) to get up and running.

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
