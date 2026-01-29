# Providers

Providers enrich the context with data from external sources. They are the bridge between your metrics and the systems you want to measure.

## Defining a Provider

Create a provider by subclassing the `Provider` base class:

```python
from checkup import Provider
from typing import Any, ClassVar


class MyProvider(Provider):
    name: ClassVar[str] = "my_provider"

    def __init__(self, config_value: str):
        self.config_value = config_value

    def provide(self) -> dict[str, Any]:
        # Fetch and return data
        return {
            "key": "value",
            "data": self.fetch_data()
        }

    def fetch_data(self):
        # Your data fetching logic
        return {"example": "data"}
```

## How Providers Work

1. Provider instances are created with configuration
2. The framework calls `provide()` on each provider
3. Returned data is added to context under the provider's namespace
4. Metrics access the data via `context[provider_name]`

```python
# Provider definition
class GitProvider(Provider):
    name: ClassVar[str] = "git"

    def provide(self) -> dict[str, Any]:
        return {"branch": "main", "commits": 100}


# Context after provider execution
context = {
    "git": {
        "branch": "main",
        "commits": 100
    }
}

# Metric access
class MyMetric(Metric):
    def calculate(self, context, metrics):
        branch = context["git"]["branch"]
```

## Provider Configuration

Providers receive configuration through `__init__`:

```python
class DatabaseProvider(Provider):
    name: ClassVar[str] = "database"

    def __init__(self, connection_string: str, timeout: int = 30):
        self.connection_string = connection_string
        self.timeout = timeout

    def provide(self) -> dict[str, Any]:
        conn = create_connection(self.connection_string, self.timeout)
        return {"connection": conn}
```

Use providers with different configurations:

```python
CheckHub()
    .with_metrics([MyMetric])
    .with_providers([
        [DatabaseProvider("postgres://prod/db")],
        [DatabaseProvider("postgres://staging/db")],
    ])
    .measure()
```

## Provider Sets

Provider sets allow running the same metrics against different contexts:

```python
CheckHub()
    .with_metrics([RepoMetrics])
    .with_providers([
        # Each inner list is a "provider set"
        [GitProvider(repo="repo-a"), EnvProvider(env="prod")],
        [GitProvider(repo="repo-b"), EnvProvider(env="prod")],
        [GitProvider(repo="repo-a"), EnvProvider(env="staging")],
    ])
    .measure()
```

Each provider set runs independently, creating separate context for metrics.

## Tag Providers

Tag providers add metadata to metrics instead of context data:

```python
from checkup import TagProvider


class ProjectTagProvider(TagProvider):
    name: ClassVar[str] = "project_tags"

    def __init__(self, project_name: str, team: str):
        self.project_name = project_name
        self.team = team

    def provide(self) -> dict[str, Any]:
        # These values are merged into metric.tags
        return {
            "project": self.project_name,
            "team": self.team
        }

    def is_tag_provider(self) -> bool:
        return True
```

Tag provider data is automatically merged into each metric's `tags` dictionary.

## Error Handling

Providers should handle errors gracefully:

```python
class RobustProvider(Provider):
    name: ClassVar[str] = "robust"

    def provide(self) -> dict[str, Any]:
        try:
            data = self.fetch_external_data()
            return {"data": data, "status": "success"}
        except ConnectionError as e:
            # Return partial data or error indicator
            return {"data": None, "status": "error", "error": str(e)}
```

For fatal errors, you can raise `ProviderError`:

```python
from checkup.errors import ProviderError


class StrictProvider(Provider):
    name: ClassVar[str] = "strict"

    def provide(self) -> dict[str, Any]:
        if not self.validate_connection():
            raise ProviderError("Cannot connect to required service")
        return self.fetch_data()
```

## Multiple Metrics, One Provider

Providers are shared across metrics. If multiple metrics declare the same provider, it runs only once:

```python
class SharedProvider(Provider):
    name: ClassVar[str] = "shared"

    def provide(self) -> dict[str, Any]:
        print("This runs only once per provider set")
        return {"shared_data": "value"}


class MetricA(Metric):
    @classmethod
    def providers(cls):
        return [SharedProvider]


class MetricB(Metric):
    @classmethod
    def providers(cls):
        return [SharedProvider]


# SharedProvider.provide() runs once, data available to both metrics
CheckHub().with_metrics([MetricA, MetricB]).measure()
```

## Best Practices

1. **Keep providers focused**: Each provider should handle one data source
2. **Use meaningful namespaces**: The `name` attribute should clearly identify the data source
3. **Make providers configurable**: Accept configuration in `__init__`
4. **Handle errors gracefully**: Don't let one failure break the entire pipeline
5. **Cache expensive operations**: If `provide()` is called multiple times, consider caching
6. **Document the data structure**: Make it clear what data your provider returns

## Example: Complete Provider

```python
from checkup import Provider
from typing import Any, ClassVar
import requests


class GitHubProvider(Provider):
    """Fetches repository information from GitHub API."""

    name: ClassVar[str] = "github"

    def __init__(self, owner: str, repo: str, token: str | None = None):
        """Initialize GitHub provider.

        Args:
            owner: Repository owner
            repo: Repository name
            token: Optional GitHub API token
        """
        self.owner = owner
        self.repo = repo
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def provide(self) -> dict[str, Any]:
        """Fetch repository data from GitHub API."""
        base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

        try:
            # Fetch repository info
            repo_response = requests.get(base_url, headers=self.headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()

            # Fetch recent commits
            commits_response = requests.get(
                f"{base_url}/commits",
                headers=self.headers,
                params={"per_page": 100}
            )
            commits_response.raise_for_status()
            commits_data = commits_response.json()

            return {
                "repository": repo_data,
                "commits": commits_data,
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "open_issues": repo_data.get("open_issues_count", 0),
            }

        except requests.RequestException as e:
            return {
                "repository": None,
                "commits": [],
                "error": str(e),
            }
```
