# Concepts Overview

CheckUp is built around three core concepts that work together to calculate and output metrics.

## The Three Pillars

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

1. **Registration**: Metrics and provider sets are registered with CheckHub
2. **Dependency Resolution**: The framework builds a dependency graph and determines execution order
3. **Validation**: Provider requirements are validated against available providers
4. **Provider Execution**: Each provider set runs to enrich context
5. **Metric Calculation**: Metrics are calculated in dependency order
6. **Result Aggregation**: Results from all provider sets are combined
7. **Materialization**: Results are output in the desired format

## Multi-Context Execution

CheckUp supports running metrics across multiple contexts (provider sets):

```python
CheckHub()
    .with_metrics([RepoMetric])
    .with_providers([
        [GitProvider(repo="repo-a")],
        [GitProvider(repo="repo-b")],
        [GitProvider(repo="repo-c")],
    ])
    .measure()
```

This calculates the same metrics for each repository, enabling comparative analysis.

## Parallel Execution

Metrics are calculated in parallel using a process pool:

- Provider sets are executed concurrently
- Within each context, metrics respect dependency order
- CPU-bound metrics can use the `PROCESS` executor
- I/O-bound metrics can use the `THREAD` executor
- Async metrics can use the `ASYNCIO` executor

## Error Handling

CheckUp provides robust error handling:

- Provider failures are captured and reported
- Individual context failures don't stop other contexts
- `MeasurementResult.errors` contains all failures
- Detailed logging is available for debugging
