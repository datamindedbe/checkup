# Concepts Overview

CheckUp is built around three core concepts that work together to calculate and output metrics.

## Providers, metrics, and materializers

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Providers  │────▶│   Metrics   │────▶│ Materializers│
│             │     │             │     │              │
│ Enrich      │     │ Calculate   │     │ Output       │
│ Context     │     │ Values      │     │ Results      │
└─────────────┘     └─────────────┘     └──────────────┘
```

### 1. Providers

[Providers](providers.md) are responsible for gathering data from external sources and enriching the context. They:

- Connect to external systems (databases, APIs, file systems)
- Fetch and organize data
- Make data available to metrics under a namespace

Example use cases:
- Reading Git repository information
- Fetching dbt project metadata
- Connecting to monitoring systems

### 2. Metrics

[Metrics](metrics.md) calculate values from the enriched context. They:

- Define what is being measured (name, description, unit)
- Declare dependencies on other metrics
- Specify which providers they need
- Calculate values and produce diagnostics

Example use cases:
- Code coverage percentage
- Number of stale branches
- dbt model test coverage

### 3. Materializers

[Materializers](materializers.md) output the calculated metrics in various formats. They:

- Format metrics for display or storage
- Support grouping and filtering
- Enable different output destinations

Available formats:
- Console (rich tables)
- CSV files
- HTML reports
- Markdown tables
- Database rows, through SQLAlchemy

## The CheckHub Orchestrator

`CheckHub` is the central orchestrator that ties everything together:

```python
from checkup import CheckHub, ConsoleMaterializer

result = (
    CheckHub()
    .with_metrics([MetricA, MetricB, MetricC])
    .with_providers([
        [ProviderX(config1)],
        [ProviderX(config2)],
    ])
    .measure()
)

result.materialize(ConsoleMaterializer(...))
```

## Execution Flow

1. **Registration**: CheckHub registers the metrics and provider sets
2. **Dependency Resolution**: The framework builds a dependency graph and determines execution order
3. **Validation**: The framework validates provider requirements against the available providers
4. **Provider Execution**: Each provider set runs to enrich context
5. **Metric Calculation**: The framework calculates metrics in dependency order
6. **Result Aggregation**: CheckHub combines the results from all provider sets
7. **Materialization**: The materializer writes the results in the format you chose

## Multi-Context Execution

CheckUp supports running metrics across multiple contexts (provider sets):

```python
(
    CheckHub()
    .with_metrics([RepoMetric])
    .with_providers([
        [GitProvider(repo="repo-a")],
        [GitProvider(repo="repo-b")],
        [GitProvider(repo="repo-c")],
    ])
    .measure()
)
```

This calculates the same metrics for each repository, enabling comparative analysis.

## Parallel Execution

CheckUp calculates metrics in parallel using a process pool:

- CheckHub runs provider sets concurrently
- Within each context, metrics respect dependency order
- CPU-bound metrics can use the `PROCESS` executor
- I/O-bound metrics can use the `THREAD` executor
- Async metrics can use the `ASYNCIO` executor

## Error Handling

CheckUp reports failures instead of hiding them:

- CheckUp captures and reports provider failures
- Each context fails independently, so the others keep running
- `MeasurementResult.errors` contains all failures
- Logging is available for debugging
