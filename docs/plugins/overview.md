# Plugins Overview

CheckUp provides a plugin system that extends the framework with domain-specific metrics and providers.

## Available Plugins

| Plugin | Package | Description |
|--------|---------|-------------|
| [Git](git.md) | `checkup-git` | Git repository metrics |
| [dbt](dbt.md) | `checkup-dbt` | dbt project metrics |
| [Python](python.md) | `checkup-python` | Python project analysis |
| [Conveyor](conveyor.md) | `checkup-conveyor` | Conveyor platform integration |

## Installing Plugins

Install plugins alongside the core package:

```bash
# Install core and desired plugins
uv add checkup checkup-git checkup-dbt
```

## Using Plugins

Import and use plugin metrics and providers like core components:

```python
from checkup import CheckHub, ConsoleMaterializer

# Import from plugin packages
from checkup_git import GitProvider, BranchCountMetric, CommitFrequencyMetric
from checkup_dbt import DbtProvider, ModelTestCoverageMetric

# Use in your pipeline
result = (
    CheckHub()
    .with_metrics([BranchCountMetric(), CommitFrequencyMetric()])
    .with_providers([
        [GitProvider(repo_path="/path/to/repo")]
    ])
    .measure()
)

result.materialize(ConsoleMaterializer(group_tag_1="domain", group_tag_2="project"))
```

## Plugin Architecture

Each plugin follows the same structure:

```
checkup-{name}/
├── pyproject.toml
├── src/
│   └── checkup_{name}/
│       ├── __init__.py
│       ├── providers.py    # Plugin-specific providers
│       └── metrics.py      # Plugin-specific metrics
└── tests/
```

Plugins:

- Depend on the core `checkup` package
- Export providers and metrics through their `__init__.py`
- Can depend on domain-specific libraries (e.g., `dbt-core`, `requests`)

## Creating Your Own Plugin

1. Create a new package structure:

```bash
mkdir -p checkup-myservice/src/checkup_myservice
cd checkup-myservice
```

2. Create `pyproject.toml`:

```toml
[project]
name = "checkup-myservice"
version = "0.1.0"
dependencies = ["checkup"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

3. Create your provider:

```python
# src/checkup_myservice/providers.py
from checkup import Provider
from typing import Any, ClassVar


class MyServiceProvider(Provider):
    name: ClassVar[str] = "myservice"

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def provide(self) -> dict[str, Any]:
        # Fetch data from your service
        return {"data": self.fetch_data()}
```

4. Create your metrics:

```python
# src/checkup_myservice/metrics.py
from checkup import Metric, Measurement, Provider
from checkup.types import Context
from .providers import MyServiceProvider


class MyServiceMetric(Metric):
    name: str = "myservice_health"
    description: str = "Health status of MyService"
    unit: str = "status"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [MyServiceProvider]

    def calculate(self, context: Context, measurements: dict) -> Measurement:
        data = context["myservice"]["data"]
        return self.measure(value=data.get("status", "unknown"))
```

5. Export in `__init__.py`:

```python
# src/checkup_myservice/__init__.py
from .providers import MyServiceProvider
from .metrics import MyServiceMetric

__all__ = ["MyServiceProvider", "MyServiceMetric"]
```

## Plugin Development Best Practices

1. **Follow naming conventions**: Use `checkup-{name}` for the package and `checkup_{name}` for the module
2. **Document thoroughly**: Include usage examples and required configuration
3. **Handle errors gracefully**: Don't let plugin failures crash the entire pipeline
4. **Write tests**: Include tests for your providers and metrics
5. **Pin dependencies carefully**: Be specific about version requirements
6. **Provide sensible defaults**: Make plugins easy to use out of the box
