# Git Plugin

The Git plugin provides metrics for analyzing Git repositories.

## Installation

```bash
pip install checkup-git
```

## Provider

### GitProvider

Fetches Git repository information.

```python
from checkup_git import GitProvider

provider = GitProvider(repo_path="/path/to/repository")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repo_path` | `str` or `Path` | Yes | Path to the Git repository |

**Context Data:**

The provider adds the following data under the `git` namespace:

```python
context["git"] = {
    "branches": [...],        # List of branch names
    "commits": [...],         # List of recent commits
    "current_branch": "...",  # Current branch name
    "remote_url": "...",      # Remote repository URL
    "last_commit": {...},     # Last commit info
}
```

## Metrics

### BranchCountMetric

Counts the number of branches in the repository.

```python
from checkup_git import BranchCountMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `branch_count` |
| Unit | `branches` |
| Dependencies | None |
| Providers | `GitProvider` |

### StaleBranchMetric

Identifies branches with no recent activity.

```python
from checkup_git import StaleBranchMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `stale_branches` |
| Unit | `branches` |
| Dependencies | None |
| Providers | `GitProvider` |

### CommitFrequencyMetric

Measures commit frequency over a time period.

```python
from checkup_git import CommitFrequencyMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `commit_frequency` |
| Unit | `commits/week` |
| Dependencies | None |
| Providers | `GitProvider` |

## Example Usage

```python
from checkup import CheckHub, ConsoleMaterializer
from checkup_git import (
    GitProvider,
    BranchCountMetric,
    StaleBranchMetric,
    CommitFrequencyMetric,
)

result = (
    CheckHub()
    .with_metrics([
        BranchCountMetric,
        StaleBranchMetric,
        CommitFrequencyMetric,
    ])
    .with_providers([
        [GitProvider(repo_path="./my-project")],
        [GitProvider(repo_path="./another-project")],
    ])
    .measure()
)

result.materialize(
    ConsoleMaterializer(group_tag_1="repository", group_tag_2="type")
)
```

## Multi-Repository Analysis

Analyze multiple repositories:

```python
from pathlib import Path

repos = [
    Path("./service-a"),
    Path("./service-b"),
    Path("./library-c"),
]

result = (
    CheckHub()
    .with_metrics([BranchCountMetric, CommitFrequencyMetric])
    .with_providers([
        [GitProvider(repo_path=repo)] for repo in repos
    ])
    .measure()
)
```
