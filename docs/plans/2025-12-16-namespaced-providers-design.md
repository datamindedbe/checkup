# Namespaced Providers Design

## Summary

Refactor the provider system from functions to abstract classes with namespaced context. Add a filesystem provider to the core library.

## Changes

### 1. Provider Base Class

New abstract base class in `src/checkup/provider.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from checkup.types import Context

class Provider(ABC):
    """Base class for context providers."""

    name: ClassVar[str]  # Namespace for this provider's data

    @classmethod
    @abstractmethod
    def provide(cls, context: Context) -> dict[str, Any]:
        """Generate data to add to context under this provider's namespace.

        Args:
            context: Current context (includes initial context and prior providers' data)

        Returns:
            Dict of data to add under context[cls.name]
        """
        ...
```

### 2. FilesystemProvider

New provider in `src/checkup/providers/filesystem.py`:

```python
from pathlib import Path
from typing import Any, ClassVar
from checkup.provider import Provider
from checkup.types import Context

class FilesystemProvider(Provider):
    """Provides filesystem path context."""

    name: ClassVar[str] = "filesystem"

    @classmethod
    def provide(cls, context: Context) -> dict[str, Any]:
        """Get filesystem path from context or default to cwd.

        Reads 'path' from initial context if present, otherwise uses cwd.

        Returns:
            {"path": Path} - resolved filesystem path
        """
        raw_path = context.get("path", Path.cwd())
        return {"path": Path(raw_path).resolve()}
```

### 3. Hub Changes

Update `_execute_providers()` for class-based providers:

```python
def _execute_providers(
    self,
    providers: list[type[Provider]],
    initial_context: Context,
) -> Context:
    """Execute all providers and build namespaced context."""
    context = initial_context.copy()

    for provider_cls in providers:
        data = provider_cls.provide(context)
        context[provider_cls.name] = data

    return context
```

Remove `initial_context` parameter from `measure()` - only use `with_contexts()`.

### 4. Metric Provider Declaration

Update `Metric.providers()` return type:

```python
@classmethod
def providers(cls) -> list[type[Provider]]:
    """Return provider classes this metric depends on."""
    return []
```

### 5. DbtManifestProvider Migration

Convert function to class in `plugins/checkup-dbt/src/checkup_dbt/provider.py`:

```python
class DbtManifestProvider(Provider):
    """Provides dbt manifest from file or live parsing."""

    name: ClassVar[str] = "dbt"

    @classmethod
    def provide(cls, context: Context) -> dict[str, Any]:
        # Same logic, returns {"manifest": Manifest}
```

### 6. Context Access Pattern

Metrics access namespaced context using provider class attribute:

```python
from checkup.providers import FilesystemProvider

path = context[FilesystemProvider.name]["path"]
```

## Files to Change

**Core library:**
- `src/checkup/provider.py` - new Provider base class
- `src/checkup/providers/__init__.py` - new providers package
- `src/checkup/providers/filesystem.py` - new FilesystemProvider
- `src/checkup/hub.py` - update provider execution, remove initial_context
- `src/checkup/metric.py` - update providers() return type
- `src/checkup/types.py` - add Provider type if needed

**Plugins:**
- `plugins/checkup-dbt/src/checkup_dbt/provider.py` - migrate to class
- `plugins/checkup-dbt/src/checkup_dbt/metrics/base.py` - update provider reference
- `plugins/checkup-dbt/src/checkup_dbt/metrics/*.py` - update context access

**Tests:**
- `tests/conftest.py` - update test providers
- `tests/test_providers.py` - update provider tests
- `tests/test_hub.py` - update hub tests
- `tests/test_integration.py` - update integration tests
