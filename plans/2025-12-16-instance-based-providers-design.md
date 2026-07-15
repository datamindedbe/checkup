# Instance-Based Providers Design

## Overview

Refactor providers from classmethod-based to instance-based, replacing `with_contexts()` with `with_providers()`. Providers receive configuration at construction time, and the framework validates that all required providers are present before running metrics.

## Provider Base Class

The `Provider` class changes from a classmethod-based interface to an instance-based one:

```python
class Provider(ABC):
    """Base class for context providers."""

    name: ClassVar[str]

    @abstractmethod
    def provide(self) -> dict[str, Any]:
        """Return data to add under this provider's namespace."""
        ...
```

Key changes:
- `provide()` becomes an instance method with no parameters
- Provider receives all configuration in `__init__`
- Still has `name` ClassVar for namespace and metric lookups

Example implementation:

```python
class DbtManifestProvider(Provider):
    name: ClassVar[str] = "dbt"

    def __init__(self, manifest_path: str | Path):
        self.manifest_path = Path(manifest_path)

    def provide(self) -> dict[str, Any]:
        with open(self.manifest_path) as f:
            manifest_dict = json.load(f)
        return {"manifest": Manifest.from_dict(manifest_dict)}
```

## TagProvider

A special built-in provider for adding arbitrary tags to metrics:

```python
class TagProvider(Provider):
    """Special provider for adding tags to metrics.

    Unlike regular providers, TagProvider's data is auto-merged
    into metric.tags by the framework rather than added to context.
    """

    name: ClassVar[str] = "tags"

    def __init__(self, **tags: Any):
        self.tags = tags

    def provide(self) -> dict[str, Any]:
        return self.tags
```

Usage:

```python
hub.with_providers([
    [DbtManifestProvider(manifest_path="./manifest.json"), TagProvider(env="prod", team="data")]
])
```

The framework recognizes `TagProvider` and merges its output into `metric.tags` instead of `context["tags"]`.

## CheckHub API Changes

The `with_contexts()` method is replaced by `with_providers()`:

```python
class CheckHub:
    def __init__(self, config_path: Path | None = None) -> None:
        self._metrics: list[type[Metric]] = []
        self._provider_sets: list[list[Provider]] = []
        self._config_path = config_path

    def with_providers(
        self,
        provider_sets: Iterable[Iterable[Provider]]
    ) -> "CheckHub":
        """Register provider sets to run metrics against.

        Each inner iterable is a set of providers for one measurement run.
        Metrics are calculated once per provider set.
        """
        for provider_set in provider_sets:
            self._provider_sets.append(list(provider_set))
        return self
```

Usage examples:

```python
# Single run
hub.with_providers([[DbtManifestProvider(manifest_path="./manifest.json")]])

# Multiple runs (e.g., multiple projects)
hub.with_providers([
    [DbtManifestProvider(manifest_path="./project_a/manifest.json"), TagProvider(project="a")],
    [DbtManifestProvider(manifest_path="./project_b/manifest.json"), TagProvider(project="b")],
])
```

## Provider Validation

The framework validates that all providers required by metrics are present before running. Validation happens at the start of `measure()`:

```python
def _validate_providers(
    self,
    metrics: list[type[Metric]],
    provider_sets: list[list[Provider]],
) -> None:
    """Validate all required providers are present in each provider set.

    Raises:
        ValueError: If any required provider is missing
    """
    # Collect all required provider classes from metrics
    required: set[type[Provider]] = set()
    for metric_cls in metrics:
        required.update(metric_cls.providers())

    # Check each provider set
    for i, provider_set in enumerate(provider_sets):
        provided_classes = {type(p) for p in provider_set}
        missing = required - provided_classes

        if missing:
            missing_names = [cls.name for cls in missing]
            raise ValueError(
                f"Provider set {i} is missing required providers: {missing_names}"
            )
```

This fails fast with a clear error message listing exactly which providers are missing and in which set.

## Execution Flow

The `measure()` method orchestrates validation, provider execution, and metric calculation:

```python
def measure(self, max_workers: int | None = None) -> MeasurementResult:
    # Build dependency graph and execution order
    graph = build_dependency_graph(self._metrics)
    execution_order = topological_sort(graph)

    # Validate providers before running anything
    provider_sets = self._provider_sets if self._provider_sets else [[]]
    self._validate_providers(list(execution_order), provider_sets)

    # Run metrics for each provider set in parallel
    all_metrics: list[Metric] = []
    all_errors: list[tuple[list[Provider], Exception]] = []

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                self._measure_single_provider_set,
                provider_set=ps,
                execution_order=execution_order,
                # ... other args
            ): ps
            for ps in provider_sets
        }
        # ... collect results
```

The `_measure_single_provider_set` method:
1. Executes each provider's `provide()` method
2. Builds namespaced context from results
3. Extracts tags from TagProvider and merges into metrics
4. Calculates metrics in dependency order

## Metric Provider Access

Metrics continue to declare provider dependencies via the `providers()` classmethod and access data via class-based lookup:

```python
class DbtModelsMetric(DbtMetric):
    name: ClassVar[str] = "dbt_models"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DbtManifestProvider]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Lookup by provider class name - unchanged
        manifest = context[DbtManifestProvider.name]["manifest"]
        self.value = len([...])
```

The framework builds the context by executing each provider instance and storing results under the provider class's `name`:

```python
def _build_context(self, provider_set: list[Provider]) -> Context:
    context: Context = {}
    for provider in provider_set:
        if not isinstance(provider, TagProvider):
            context[provider.name] = provider.provide()
    return context
```

Metrics are decoupled from specific instances - they only know about provider classes.

## Migration and Breaking Changes

**Breaking changes:**

1. `with_contexts()` removed - replaced by `with_providers()`
2. `Provider.provide(cls, context)` becomes `Provider.provide(self)` - instance method, no context param
3. Provider classes must now have `__init__` accepting configuration
4. `FilesystemProvider` removed

**Migration path for DbtManifestProvider:**

Before:
```python
CheckHub()
    .with_metrics([DbtModelsMetric])
    .with_contexts([{"manifest_path": "./manifest.json", "project": "myproject"}])
    .measure()
```

After:
```python
CheckHub()
    .with_metrics([DbtModelsMetric])
    .with_providers([[
        DbtManifestProvider(manifest_path="./manifest.json"),
        TagProvider(project="myproject"),
    ]])
    .measure()
```
