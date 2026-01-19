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
├── run           # Execute metrics (main command)
├── list          # List available metrics/providers
├── validate      # Validate configuration
├── init          # Generate starter configuration
└── version       # Show version info
```

### Command Details

#### `checkup run`

Primary command for executing metrics.

```bash
# Run with config file
checkup run -c checkup.yaml

# Run with config and output to CSV
checkup run -c checkup.yaml -o results.csv

# Run specific metrics only
checkup run -c checkup.yaml --metric dbt_models --metric dbt_tests

# Run with specific output format
checkup run -c checkup.yaml --format json

# Run with verbose logging
checkup run -c checkup.yaml -v

# Run with max workers
checkup run -c checkup.yaml --workers 4

# Run and include indirect (dependency) metrics in output
checkup run -c checkup.yaml --include-indirect
```

**Options:**

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--config` | `-c` | Path | `checkup.yaml` | Configuration file path |
| `--output` | `-o` | Path | None | Output file path (format inferred from extension) |
| `--format` | `-f` | Choice | `console` | Output format: console, csv, json, html |
| `--metric` | `-m` | List | All | Specific metrics to run (can repeat) |
| `--workers` | `-w` | Int | CPU count | Max parallel workers |
| `--include-indirect` | | Flag | False | Include dependency metrics in output |
| `--verbose` | `-v` | Count | 0 | Increase verbosity (-v, -vv, -vvv) |
| `--quiet` | `-q` | Flag | False | Suppress non-error output |
| `--dry-run` | | Flag | False | Validate and show plan without executing |
| `--fail-on-error` | | Flag | False | Exit with error code if any metric fails |

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration error |
| 2 | Execution error (with `--fail-on-error`) |
| 3 | Invalid arguments |

---

#### `checkup list`

Discover available metrics and providers.

```bash
# List all available metrics
checkup list metrics

# List metrics with details
checkup list metrics --verbose

# List metrics from specific plugin
checkup list metrics --plugin checkup-dbt

# List all providers
checkup list providers

# List in JSON format (for tooling)
checkup list metrics --format json

# Search metrics by name pattern
checkup list metrics --filter "dbt_*"
```

**Subcommands:**

- `checkup list metrics` - List available metric classes
- `checkup list providers` - List available provider classes
- `checkup list plugins` - List installed plugins

**Output Example (metrics):**

```
Available Metrics:

checkup-dbt:
  dbt_models              Count of dbt models                    [count]
  dbt_columns             Count of dbt columns                   [count]
  dbt_tests               Count of dbt tests                     [count]
  dbt_models_with_desc    Models with descriptions               [count]
  dbt_column_test_cov     Column test coverage                   [percentage]
  ...

checkup-python:
  python_version          Python interpreter version             [version]

Total: 18 metrics from 2 plugins
```

---

#### `checkup validate`

Validate configuration without executing.

```bash
# Validate config file
checkup validate -c checkup.yaml

# Validate with verbose output
checkup validate -c checkup.yaml -v
```

**Checks performed:**

1. YAML syntax validity
2. Required fields present
3. Referenced metrics exist
4. Referenced providers exist
5. Metric dependencies resolvable
6. Provider requirements satisfiable
7. No duplicate metric names

**Output Example:**

```
Validating checkup.yaml...

✓ YAML syntax valid
✓ Configuration schema valid
✓ All 5 metrics found
✓ All 2 providers found
✓ Dependency graph valid (no cycles)
✓ Provider requirements satisfied

Configuration is valid.
```

---

#### `checkup init`

Generate starter configuration.

```bash
# Interactive initialization
checkup init

# Generate for specific plugins
checkup init --plugin checkup-dbt

# Generate to specific file
checkup init -o my-config.yaml

# Non-interactive with defaults
checkup init --defaults
```

**Generated config example:**

```yaml
# checkup.yaml - Generated by checkup init

# Metrics to calculate
metrics:
  - checkup_dbt.DbtModelsMetric
  - checkup_dbt.DbtTestsMetric
  - checkup_dbt.DbtColumnTestCoverageMetric

# Provider configurations
providers:
  - type: checkup_dbt.DbtManifestProvider
    # manifest_path: ./target/manifest.json  # Optional: path to pre-built manifest

# Output configuration
output:
  format: console
  group_by:
    - domain
    - project

# Optional: metric-specific configuration
metric_config:
  # Example: configure naming convention checker
  # dbt_naming_convention:
  #   model_prefix: stg_
```

---

#### `checkup version`

Display version information.

```bash
checkup version

# Output:
# checkup 0.1.0
# Python 3.12.0
# Plugins:
#   checkup-dbt 0.1.0
#   checkup-python 0.1.0
```

---

## Configuration File Format

### Extended Schema

```yaml
# checkup.yaml

# === METRICS ===
# List of metrics to calculate
# Can be fully qualified names or short names (if unambiguous)
metrics:
  # Fully qualified
  - checkup_dbt.DbtModelsMetric
  - checkup_dbt.DbtTestsMetric

  # Or use short names (resolved via plugin discovery)
  - DbtColumnsMetric
  - python_version  # Resolved by metric.name attribute

# === PROVIDERS ===
# Provider instances with their configuration
providers:
  # Provider sets - each set runs independently (parallel)
  - set:
      - type: checkup_dbt.DbtManifestProvider
        manifest_path: ./project_a/target/manifest.json
      - type: checkup.TagProvider
        tags:
          project: project_a
          domain: sales

  - set:
      - type: checkup_dbt.DbtManifestProvider
        manifest_path: ./project_b/target/manifest.json
      - type: checkup.TagProvider
        tags:
          project: project_b
          domain: marketing

# === OUTPUT ===
output:
  # Default format for console output
  format: console  # console | csv | json | html

  # Grouping for console/html output
  group_by:
    level1: domain
    level2: project

  # File output (optional)
  file: ./reports/metrics.html

  # Include indirect metrics (dependencies)
  include_indirect: false

# === METRIC CONFIG ===
# Per-metric configuration (passed to metric __init__)
metric_config:
  dbt_naming_convention:
    model_prefix: stg_

  custom_threshold_metric:
    threshold: 0.8
    warning_level: 0.6

# === EXECUTION ===
execution:
  # Max parallel workers
  workers: 4

  # Fail fast on provider errors
  fail_fast: true

  # Timeout per provider set (seconds)
  timeout: 300
```

### Minimal Configuration

```yaml
# Minimal checkup.yaml for dbt project
metrics:
  - DbtModelsMetric
  - DbtTestsMetric
  - DbtColumnTestCoverageMetric

providers:
  - set:
      - type: DbtManifestProvider
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
# In a dbt project directory
cd my-dbt-project
checkup init --plugin checkup-dbt
checkup run
```

### Scenario 2: Multi-Project Report

```yaml
# checkup.yaml
metrics:
  - DbtModelsMetric
  - DbtColumnTestCoverageMetric

providers:
  - set:
      - type: DbtManifestProvider
        manifest_path: ./projects/sales/target/manifest.json
      - type: TagProvider
        tags: {project: sales}
  - set:
      - type: DbtManifestProvider
        manifest_path: ./projects/marketing/target/manifest.json
      - type: TagProvider
        tags: {project: marketing}

output:
  format: html
  file: ./reports/metrics.html
  group_by:
    level1: project
```

```bash
checkup run -c checkup.yaml
```

### Scenario 3: CI/CD Integration

```bash
# In CI pipeline
checkup run -c checkup.yaml --format json -o metrics.json --fail-on-error

# Parse with jq
cat metrics.json | jq '.metrics[] | select(.name == "dbt_column_test_cov") | .value'
```

### Scenario 4: Comparing Metrics

```bash
# Run for baseline
checkup run -c checkup.yaml -o baseline.csv

# After changes
checkup run -c checkup.yaml -o current.csv

# Compare (using external tool)
diff baseline.csv current.csv
```

---

## Future Considerations

1. **Thresholds and Alerts**: Define acceptable ranges for metrics
2. **Historical Tracking**: Store metrics over time for trend analysis
3. **Remote Providers**: Fetch data from APIs (GitHub, Jira, etc.)
4. **Custom Materializers**: Plugin support for output formats
5. **Interactive Mode**: REPL for exploring metrics
6. **Configuration Inheritance**: Base configs with project overrides
