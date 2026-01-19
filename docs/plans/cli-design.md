# Checkup CLI Design

## Overview

This document outlines the design for a comprehensive CLI for the checkup metrics framework. The CLI will provide a user-friendly interface for running metrics, discovering available metrics/providers, and validating configurations.

## Design Goals

1. **Declarative configuration** - Define what to measure in YAML, not code
2. **Plugin discovery** - Automatically find installed metrics and providers
3. **Multiple output formats** - Console, CSV, HTML, JSON
4. **Composable** - Chain with other Unix tools
5. **Progressive disclosure** - Simple for basic use, powerful for advanced use

---

## Provider Configuration Challenge

### The Problem

Providers in checkup are **instance-based** with constructor arguments:

```python
# Current programmatic API
CheckHub()
    .with_providers([
        [DbtManifestProvider(manifest_path="./project_a/manifest.json"), TagProvider(project="a")],
        [DbtManifestProvider(manifest_path="./project_b/manifest.json"), TagProvider(project="b")],
    ])
    .measure()
```

Key complexity factors:
1. **Provider sets run in parallel** - each produces a separate measurement context
2. **Constructor arguments vary** - `DbtManifestProvider` takes paths, `TagProvider` takes arbitrary kwargs
3. **Some providers need complex initialization** - database connections, API clients, etc.
4. **Type safety** - Python's type system catches errors that YAML cannot

### Recommendation: Python Configuration Files (Airflow-style)

Following Airflow's proven pattern, use **Python files as the configuration format**. The CLI discovers and operates on these files.

```python
# checkup_dbt.py - A "checkup" (like an Airflow DAG file)
from checkup import Checkup
from checkup_dbt import DbtManifestProvider, DbtModelsMetric, DbtTestsMetric
from checkup.providers.tags import TagProvider

# Define the measurement configuration
checkup = Checkup(
    name="dbt-metrics",
    description="dbt project health metrics",
)

checkup.add_metrics([
    DbtModelsMetric,
    DbtTestsMetric,
])

checkup.add_provider_set([
    DbtManifestProvider(manifest_path="./project_a/target/manifest.json"),
    TagProvider(project="project_a", domain="sales"),
])

checkup.add_provider_set([
    DbtManifestProvider(manifest_path="./project_b/target/manifest.json"),
    TagProvider(project="project_b", domain="marketing"),
])
```

**CLI usage:**
```bash
checkup run checkup_dbt.py              # Run the checkup
checkup run checkup_dbt.py -o report.html  # Output to HTML
checkup validate checkup_dbt.py         # Validate without running
checkup list checkup_dbt.py             # List metrics/providers
```

**Why this approach:**

| Benefit | Explanation |
|---------|-------------|
| **Familiar pattern** | Data engineers know this from Airflow |
| **Full type safety** | IDE autocomplete, mypy, runtime validation |
| **No config split** | Single source of truth in one file |
| **Maximum flexibility** | Loops, conditionals, imports, functions |
| **Testable** | Can unit test configuration logic |
| **Discoverable** | CLI can scan directories for checkups |

### Alternative: Builder Pattern (Current API)

For users who prefer the existing fluent API:

```python
# checkup_dbt.py
from checkup import CheckHub
from checkup_dbt import DbtManifestProvider, DbtModelsMetric
from checkup.providers.tags import TagProvider

hub = (
    CheckHub(name="dbt-metrics")
    .with_metrics([DbtModelsMetric])
    .with_providers([
        [DbtManifestProvider(manifest_path="./manifest.json"), TagProvider(project="a")],
    ])
)
```

The CLI detects either a `checkup` or `hub` variable in the module.

### Dynamic Configuration Example

The Python approach shines for dynamic setups:

```python
# checkup_all_projects.py
from pathlib import Path
from checkup import Checkup
from checkup_dbt import DbtManifestProvider, DbtModelsMetric, DbtColumnTestCoverageMetric
from checkup.providers.tags import TagProvider

checkup = Checkup(name="all-dbt-projects")

checkup.add_metrics([
    DbtModelsMetric,
    DbtColumnTestCoverageMetric,
])

# Dynamically discover all dbt projects
for project_dir in Path("./projects").iterdir():
    manifest = project_dir / "target" / "manifest.json"
    if manifest.exists():
        checkup.add_provider_set([
            DbtManifestProvider(manifest_path=manifest),
            TagProvider(
                project=project_dir.name,
                domain=project_dir.parent.name,
            ),
        ])
```

### Why Not YAML?

| YAML Approach | Python Approach |
|---------------|-----------------|
| Two files (YAML + Python for complex cases) | One file |
| Runtime type errors | Caught by IDE/mypy |
| Limited expressiveness | Full language power |
| Custom DSL to learn | Just Python |
| Hard to test | Standard pytest |
| Magic string references | Direct imports |

---

## CLI Framework

**Recommendation: `typer`**

| Criteria | typer | click | argparse |
|----------|-------|-------|----------|
| Type hints | Native | Manual | Manual |
| Auto-completion | Built-in | Plugin | Manual |
| Help generation | Automatic | Automatic | Basic |
| Learning curve | Low | Medium | High |
| Dependencies | Minimal | Minimal | None |

Typer is built on Click but leverages Python type hints for automatic argument parsing, making it ideal for a Python 3.12+ codebase.

---

## Command Structure

```
checkup
├── run           # Execute a checkup
├── validate      # Validate a checkup without running
├── list          # List metrics/providers in a checkup
├── init          # Generate starter checkup
└── version       # Show version info
```

### Command Details

#### `checkup run <checkup>`

Execute metrics defined in a Python checkup.

```bash
# Run a checkup
checkup run checkup_dbt.py

# Output to file (format inferred from extension)
checkup run checkup_dbt.py -o results.csv
checkup run checkup_dbt.py -o report.html
checkup run checkup_dbt.py -o metrics.json

# Explicit output format
checkup run checkup_dbt.py --format json

# Run specific metrics only
checkup run checkup_dbt.py --metric dbt_models --metric dbt_tests

# Control parallelism
checkup run checkup_dbt.py --workers 4

# Verbose logging
checkup run checkup_dbt.py -v

# Include dependency metrics in output
checkup run checkup_dbt.py --include-indirect

# Dry run - validate and show plan without executing
checkup run checkup_dbt.py --dry-run

# CI mode - exit with error if any metric calculation fails
checkup run checkup_dbt.py --fail-on-error
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `checkup` | Path | Yes | Python checkup to execute |

**Options:**

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--output` | `-o` | Path | None | Output file (format from extension) |
| `--format` | `-f` | Choice | `console` | Output format: console, csv, json, html |
| `--metric` | `-m` | List | All | Specific metrics to run (repeatable) |
| `--workers` | `-w` | Int | CPU count | Max parallel workers |
| `--include-indirect` | | Flag | False | Include dependency metrics in output |
| `--group-by` | `-g` | Str | None | Tag names for grouping (e.g., `-g domain -g project`) |
| `--verbose` | `-v` | Count | 0 | Increase verbosity (-v, -vv, -vvv) |
| `--quiet` | `-q` | Flag | False | Suppress non-error output |
| `--dry-run` | | Flag | False | Validate and show plan without executing |
| `--fail-on-error` | | Flag | False | Exit with error code if any metric fails |

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration/checkup error |
| 2 | Metric execution error (with `--fail-on-error`) |
| 3 | Invalid arguments |

---

#### `checkup list <checkup>`

Inspect a checkup's metrics and providers.

```bash
# List metrics in a checkup
checkup list checkup_dbt.py

# Detailed output
checkup list checkup_dbt.py --verbose

# JSON format for tooling
checkup list checkup_dbt.py --format json

# List only metrics
checkup list checkup_dbt.py --metrics

# List only providers
checkup list checkup_dbt.py --providers
```

**Output Example:**

```
Checkup: checkup_dbt.py
Name: dbt-metrics
Description: dbt project health metrics

Metrics (3):
  dbt_models              Count of dbt models                    [count]
  dbt_tests               Count of dbt tests                     [count]
  dbt_column_test_cov     Column test coverage                   [percentage]

Provider Sets (2):
  Set 1:
    - DbtManifestProvider (manifest_path=./project_a/target/manifest.json)
    - TagProvider (project=project_a, domain=sales)
  Set 2:
    - DbtManifestProvider (manifest_path=./project_b/target/manifest.json)
    - TagProvider (project=project_b, domain=marketing)

Dependency Graph:
  dbt_column_test_cov
  └── dbt_tested_columns
      └── dbt_columns
```

---

#### `checkup validate <checkup>`

Validate a checkup without executing.

```bash
# Validate checkup
checkup validate checkup_dbt.py

# Verbose output
checkup validate checkup_dbt.py -v
```

**Checks performed:**

1. Python syntax valid
2. Checkup or hub variable found
3. All metric classes importable
4. All provider instances valid
5. Dependency graph valid (no cycles)
6. Provider requirements satisfied
7. No duplicate metric names
8. Metrics are pickleable (for ProcessPoolExecutor)

**Output Example:**

```
Validating checkup_dbt.py...

✓ Python syntax valid
✓ Checkup 'dbt-metrics' found
✓ 3 metrics registered
✓ 2 provider sets configured
✓ Dependency graph valid (no cycles)
✓ Provider requirements satisfied
✓ All metrics pickleable

Checkup is valid.
```

---

#### `checkup init`

Generate a starter checkup, optionally tailored to a specific plugin.

```bash
# Interactive - prompts for plugin selection and configuration
checkup init

# Generate for specific plugin
checkup init --plugin dbt

# Output to specific file
checkup init --plugin dbt -o my_checkup.py

# Non-interactive with defaults
checkup init --plugin dbt --defaults

# List available plugins that support init
checkup init --list
```

**How `checkup init` works:**

The init command generates a starter checkup. It's intentionally simple - the user customizes it for their specific setup.

```bash
# Basic: generate minimal template
checkup init

# With plugin: get plugin-specific boilerplate
checkup init --plugin dbt

# Output to specific file
checkup init -o my_checkup.py
```

**Basic template (no plugin):**

```python
# checkup.py - Generated by checkup init
"""Project health metrics."""

from checkup import Checkup
from checkup.providers.tags import TagProvider

checkup = Checkup(
    name="my-metrics",
    description="Project health metrics",
)

# Add your metrics here
# checkup.add_metrics([...])

# Add your provider sets here
# Each provider set represents one context (project, environment, etc.)
# checkup.add_provider_set([
#     SomeProvider(...),
#     TagProvider(project="my-project"),
# ])
```

**Plugin-specific template (`--plugin dbt`):**

```python
# checkup.py - Generated by checkup init --plugin dbt
"""dbt project health metrics."""

from pathlib import Path
from checkup import Checkup
from checkup_dbt import (
    DbtManifestProvider,
    DbtModelsMetric,
    DbtTestsMetric,
    DbtColumnTestCoverageMetric,
)
from checkup.providers.tags import TagProvider

checkup = Checkup(
    name="dbt-metrics",
    description="dbt project health metrics",
)

checkup.add_metrics([
    DbtModelsMetric,
    DbtTestsMetric,
    DbtColumnTestCoverageMetric,
])

# Configure your dbt project(s) here
# Option 1: Single project with pre-built manifest
checkup.add_provider_set([
    DbtManifestProvider(manifest_path="./target/manifest.json"),
    TagProvider(project="my-project"),
])

# Option 2: Single project, parse on-the-fly
# checkup.add_provider_set([
#     DbtManifestProvider(dbt_project_dir="./"),
#     TagProvider(project="my-project"),
# ])

# Option 3: Multiple projects (uncomment and customize)
# PROJECTS = ["sales", "marketing", "finance"]
# for project in PROJECTS:
#     checkup.add_provider_set([
#         DbtManifestProvider(manifest_path=f"./{project}/target/manifest.json"),
#         TagProvider(project=project),
#     ])
```

**Plugin template registration:**

Plugins register templates via entry points:

```toml
# In checkup-dbt's pyproject.toml
[project.entry-points."checkup.init_templates"]
dbt = "checkup_dbt.templates:get_init_template"
```

```python
# checkup_dbt/templates.py
def get_init_template() -> str:
    """Return the init template for dbt projects."""
    return '''
"""dbt project health metrics."""

from pathlib import Path
from checkup import Checkup
from checkup_dbt import (
    DbtManifestProvider,
    DbtModelsMetric,
    ...
)
...
'''
```

**Available plugins:**

```
$ checkup init --list

Available plugins:
  dbt      - dbt project health metrics
  python   - Python project metrics
  git      - Git repository metrics
  conveyor - Conveyor deployment metrics
```

---

#### `checkup version`

Display version information.

```bash
checkup version

# Output:
# checkup 0.1.0
# Python 3.12.0
# Installed plugins:
#   checkup-dbt 0.1.0
#   checkup-python 0.1.0
#   checkup-git 0.1.0
```

---

## Checkup API

A checkup is a Python module containing a `checkup` or `hub` variable that defines the measurement configuration.

### Checkup Class

```python
from checkup import Checkup

checkup = Checkup(
    name="my-metrics",                    # Required: unique identifier
    description="My project metrics",     # Optional: human-readable description
)

# Add metrics (list of metric classes)
checkup.add_metrics([MetricA, MetricB])

# Add provider set (list of provider instances)
checkup.add_provider_set([ProviderA(), ProviderB()])

# Add multiple provider sets at once
checkup.add_provider_sets([
    [ProviderA(config="a"), TagProvider(env="a")],
    [ProviderA(config="b"), TagProvider(env="b")],
])
```

### Using the Existing Builder API

The CLI also supports the existing `CheckHub` builder pattern:

```python
from checkup import CheckHub

hub = (
    CheckHub(name="my-metrics")
    .with_metrics([MetricA, MetricB])
    .with_providers([
        [ProviderA(), TagProvider(env="prod")],
    ])
)
```

The CLI detects either `checkup` or `hub` at module level.

### Complete Example

```python
# checkup_dbt.py
"""dbt project health metrics for all projects."""

from pathlib import Path
from checkup import Checkup
from checkup_dbt import (
    DbtManifestProvider,
    DbtModelsMetric,
    DbtTestsMetric,
    DbtModelsWithDescriptionMetric,
    DbtColumnTestCoverageMetric,
)
from checkup.providers.tags import TagProvider

# Configuration
PROJECTS_DIR = Path("./dbt_projects")
DOMAIN_MAP = {
    "sales-mart": "sales",
    "marketing-analytics": "marketing",
    "finance-reporting": "finance",
}

# Create checkup
checkup = Checkup(
    name="dbt-health",
    description="dbt project health metrics across all projects",
)

# Define metrics to calculate
checkup.add_metrics([
    DbtModelsMetric,
    DbtTestsMetric,
    DbtModelsWithDescriptionMetric,
    DbtColumnTestCoverageMetric,
])

# Dynamically discover and configure provider sets
for project_dir in sorted(PROJECTS_DIR.iterdir()):
    if not project_dir.is_dir():
        continue

    manifest = project_dir / "target" / "manifest.json"
    if not manifest.exists():
        print(f"Warning: No manifest found for {project_dir.name}")
        continue

    checkup.add_provider_set([
        DbtManifestProvider(manifest_path=manifest),
        TagProvider(
            project=project_dir.name,
            domain=DOMAIN_MAP.get(project_dir.name, "other"),
        ),
    ])

# Validate at import time (optional, helps catch errors early)
checkup.validate()
```

### Metric Configuration

Pass configuration to metrics via the checkup:

```python
from checkup_dbt import DbtModelsNotAdheringToNamingConventionMetric

checkup = Checkup(name="configured-metrics")

# Configure specific metrics
checkup.add_metrics([
    DbtModelsNotAdheringToNamingConventionMetric,
], config={
    "dbt_naming_convention": {
        "model_prefix": "stg_",
        "staging_prefix": "stg_",
        "mart_prefix": "fct_",
    }
})
```

### Environment-Based Configuration

```python
import os
from checkup import Checkup

ENV = os.getenv("CHECKUP_ENV", "dev")

checkup = Checkup(name=f"metrics-{ENV}")

if ENV == "prod":
    # Production: all projects
    projects = ["sales", "marketing", "finance"]
else:
    # Dev: only sales for faster iteration
    projects = ["sales"]

for project in projects:
    checkup.add_provider_set([
        DbtManifestProvider(manifest_path=f"./{project}/target/manifest.json"),
        TagProvider(project=project, environment=ENV),
    ])
```

---

## Plugin Discovery

### Entry Points Mechanism

Plugins register their metrics and providers via Python entry points:

```toml
# In plugin's pyproject.toml
[project.entry-points."checkup.metrics"]
dbt_models = "checkup_dbt:DbtModelsMetric"
dbt_tests = "checkup_dbt:DbtTestsMetric"
# ... more metrics

[project.entry-points."checkup.providers"]
dbt_manifest = "checkup_dbt:DbtManifestProvider"
```

### Discovery API

```python
# src/checkup/discovery.py

from importlib.metadata import entry_points

def discover_metrics() -> dict[str, type[Metric]]:
    """Discover all registered metrics from installed plugins."""
    metrics = {}
    eps = entry_points(group="checkup.metrics")
    for ep in eps:
        metrics[ep.name] = ep.load()
    return metrics

def discover_providers() -> dict[str, type[Provider]]:
    """Discover all registered providers from installed plugins."""
    providers = {}
    eps = entry_points(group="checkup.providers")
    for ep in eps:
        providers[ep.name] = ep.load()
    return providers

def discover_plugins() -> list[str]:
    """List all installed checkup plugins."""
    # Plugins follow naming convention: checkup-*
    from importlib.metadata import distributions
    return [d.metadata["Name"] for d in distributions()
            if d.metadata["Name"].startswith("checkup-")]
```

---

## Output Formats

### Console (Default)

Rich-formatted tables grouped by tags (current `ConsoleMaterializer` behavior).

### CSV

```csv
name,value,unit,diagnostic,description,domain,project
dbt_models,42,count,,Count of dbt models,sales,project_a
dbt_tests,128,count,,Count of dbt tests,sales,project_a
```

### JSON

```json
{
  "metadata": {
    "timestamp": "2025-01-19T10:30:00Z",
    "checkup_version": "0.1.0",
    "duration_seconds": 2.5
  },
  "metrics": [
    {
      "name": "dbt_models",
      "value": 42,
      "unit": "count",
      "description": "Count of dbt models",
      "diagnostic": "",
      "tags": {
        "domain": "sales",
        "project": "project_a"
      }
    }
  ],
  "errors": []
}
```

### HTML

Current `HTMLMaterializer` with Bootstrap accordions.

---

## Implementation Structure

```
src/checkup/
├── __init__.py          # Existing + CLI entry point
├── cli/
│   ├── __init__.py
│   ├── app.py           # Main typer app
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── run.py       # checkup run
│   │   ├── list.py      # checkup list
│   │   ├── validate.py  # checkup validate
│   │   ├── init.py      # checkup init
│   │   └── version.py   # checkup version
│   ├── config.py        # Extended config loading
│   └── discovery.py     # Plugin discovery
├── hub.py               # Existing
├── ...
```

### Main App (`cli/app.py`)

```python
"""Checkup CLI application."""

import typer
from rich.console import Console

from checkup.cli.commands import run, list_cmd, validate, init, version

app = typer.Typer(
    name="checkup",
    help="Extensible metrics calculation framework",
    no_args_is_help=True,
)

# Register commands
app.add_typer(run.app, name="run")
app.add_typer(list_cmd.app, name="list")
app.command()(validate.validate)
app.command()(init.init)
app.command()(version.version)

console = Console()

def main():
    """CLI entry point."""
    app()
```

### Run Command (`cli/commands/run.py`)

```python
"""Run command implementation."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from checkup import CheckHub, ConsoleMaterializer, CSVMaterializer, HTMLMaterializer
from checkup.cli.config import load_cli_config
from checkup.cli.discovery import resolve_metrics, resolve_providers

app = typer.Typer()
console = Console()

@app.callback(invoke_without_command=True)
def run(
    config: Annotated[Path, typer.Option("--config", "-c", help="Config file")] = Path("checkup.yaml"),
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output file")] = None,
    format: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "console",
    metrics: Annotated[Optional[list[str]], typer.Option("--metric", "-m", help="Specific metrics")] = None,
    workers: Annotated[Optional[int], typer.Option("--workers", "-w", help="Max workers")] = None,
    include_indirect: Annotated[bool, typer.Option(help="Include dependency metrics")] = False,
    verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity")] = 0,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet mode")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate only")] = False,
    fail_on_error: Annotated[bool, typer.Option(help="Exit 2 on metric errors")] = False,
):
    """Execute metrics measurement."""
    # Load and validate config
    cfg = load_cli_config(config)

    # Resolve metrics and providers
    metric_classes = resolve_metrics(metrics or cfg.metrics)
    provider_sets = resolve_providers(cfg.providers)

    if dry_run:
        console.print("[green]✓[/green] Configuration valid")
        console.print(f"  Metrics: {len(metric_classes)}")
        console.print(f"  Provider sets: {len(provider_sets)}")
        return

    # Execute
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        progress.add_task("Measuring metrics...", total=None)

        result = (
            CheckHub(config_path=config)
            .with_metrics(metric_classes)
            .with_providers(provider_sets)
            .measure(max_workers=workers)
        )

    # Output results
    materializer = _get_materializer(format, output, cfg, include_indirect)
    result.materialize(materializer)

    # Handle errors
    if result.errors and fail_on_error:
        raise typer.Exit(2)
```

---

## Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # Existing
    "jinja2>=3.1.6",
    "pydantic>=2.11.7",
    "pyyaml>=6.0",
    "rich>=13.0",
    # New for CLI
    "typer>=0.12.0",
]
```

---

## Migration Path

### Phase 1: Core CLI
- Implement `run`, `version` commands
- Basic config file support
- Console output

### Phase 2: Discovery
- Plugin entry points
- `list` command
- `validate` command

### Phase 3: Enhanced Features
- `init` command
- JSON output format
- Progress reporting
- Shell completion

### Phase 4: Advanced
- `--dry-run` with dependency visualization
- Watch mode for continuous measurement
- Webhook/notification support

---

## Example Usage Scenarios

### Scenario 1: Quick dbt Project Check

```bash
# Generate starter checkup
checkup init --plugin dbt -o checkup_dbt.py

# Edit the generated file to point to your manifest
# Then run
checkup run checkup_dbt.py
```

### Scenario 2: Multi-Project Report

```python
# checkup_projects.py
from pathlib import Path
from checkup import Checkup
from checkup_dbt import DbtManifestProvider, DbtModelsMetric, DbtColumnTestCoverageMetric
from checkup.providers.tags import TagProvider

checkup = Checkup(name="multi-project")
checkup.add_metrics([DbtModelsMetric, DbtColumnTestCoverageMetric])

for project in ["sales", "marketing", "finance"]:
    checkup.add_provider_set([
        DbtManifestProvider(manifest_path=f"./projects/{project}/target/manifest.json"),
        TagProvider(project=project),
    ])
```

```bash
checkup run checkup_projects.py -o report.html -g project
```

### Scenario 3: CI/CD Integration

```yaml
# .github/workflows/metrics.yml
name: Metrics Check
on: [push]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install checkup checkup-dbt
      - run: dbt parse  # Generate manifest
      - run: checkup validate checkup_ci.py
      - run: checkup run checkup_ci.py --format json -o metrics.json --fail-on-error
      - uses: actions/upload-artifact@v4
        with:
          name: metrics
          path: metrics.json
```

```bash
# Parse metrics in CI
cat metrics.json | jq '.metrics[] | select(.name == "dbt_column_test_cov") | .value'
```

### Scenario 4: Comparing Metrics Over Time

```bash
# Run for baseline (e.g., main branch)
checkup run checkup_dbt.py -o baseline.csv

# After changes (e.g., feature branch)
checkup run checkup_dbt.py -o current.csv

# Compare
diff baseline.csv current.csv

# Or use a dedicated comparison tool
checkup diff baseline.csv current.csv  # Future feature
```

### Scenario 5: Development Workflow

```python
# checkup_dev.py - Fast iteration during development
import os
from checkup import Checkup
from checkup_dbt import DbtManifestProvider, DbtModelsMetric

checkup = Checkup(name="dev-check")

# Only run lightweight metrics during development
checkup.add_metrics([DbtModelsMetric])

# Use dbt_project_dir to parse on-the-fly (no pre-built manifest needed)
checkup.add_provider_set([
    DbtManifestProvider(dbt_project_dir="./"),
])
```

```bash
# Quick check during development
checkup run checkup_dev.py
```

---

## Future Considerations

1. **Thresholds and Alerts**: Define acceptable ranges for metrics
2. **Historical Tracking**: Store metrics over time for trend analysis
3. **Remote Providers**: Fetch data from APIs (GitHub, Jira, etc.)
4. **Custom Materializers**: Plugin support for output formats
5. **Interactive Mode**: REPL for exploring metrics
6. **Configuration Inheritance**: Base configs with project overrides
