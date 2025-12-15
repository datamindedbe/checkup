# Checkup

Extensible metrics calculation framework with dependency resolution and context enrichment.

## Features

- **Extensible metrics** - Define custom metrics as Pydantic models
- **Dependency resolution** - Metrics can depend on other metrics
- **Context providers** - Enrich context from environment (credentials, configs)
- **YAML configuration** - Configure metric bounds and parameters
- **Multiple outputs** - Materialize to console, HTML, CSV, etc.
- **Type-safe** - Full type hints and Pydantic validation

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from checkup import CheckHub, Metric, ConsoleMaterializer
from checkup.types import Context

# Define a metric
class PythonVersionMetric(Metric):
    name: str = "python_version"
    description: str = "Python version check"
    unit: str = "version"
    min: str = "3.11.0"

    def calculate(self, context: Context, metrics: dict) -> None:
        import sys
        self.value = f"{sys.version_info.major}.{sys.version_info.minor}"

# Run metrics
(
    CheckHub()
    .with_metrics([PythonVersionMetric])
    .measure()
    .materialize(ConsoleMaterializer())
)
```

## Configuration

Create `checkup.yaml`:

```yaml
metrics:
  python_version:
    min: "3.11.0"
    max: "3.12.99"
```

Use with CheckHub:

```python
from pathlib import Path

CheckHub(config_path=Path("checkup.yaml"))
```

## Architecture

See [Design Document](docs/plans/2025-12-15-metrics-framework-design.md) for details.

### Key Concepts

- **Metrics** - Calculate values from context
- **Providers** - Functions that enrich context (shared across metrics)
- **Dependencies** - Metrics can depend on other metrics' values
- **Materializers** - Output formats (Console, HTML, CSV, etc.)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=checkup
```

## License

MIT
