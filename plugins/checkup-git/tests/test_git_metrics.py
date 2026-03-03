from pathlib import Path

from checkup_git import (
    GitDaysSinceLastUpdateMetric,
    GitProvider,
    GitTrackedFileCountMetric,
)

from checkup.hub import CheckHub


def test_days_since_last_update_metric(git_repo: Path):
    """Test days since last update metric."""
    result = (
        CheckHub()
        .with_metrics([GitDaysSinceLastUpdateMetric])
        .with_providers([[GitProvider(repo_path=git_repo)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "git_days_since_last_update"
    assert metric.value == 0  # Just committed, should be 0 days


def test_tracked_file_count_metric(git_repo: Path):
    """Test tracked file count metric."""
    result = (
        CheckHub()
        .with_metrics([GitTrackedFileCountMetric])
        .with_providers([[GitProvider(repo_path=git_repo)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "git_tracked_file_count"
    assert metric.value == 1  # One file (README.md) in the fixture


class DagCountMetric(GitTrackedFileCountMetric):
    name = "dag_count"
    description = "Number of DAG files"
    pattern: str = "dags/*.py"


def test_tracked_file_count_with_pattern(tmp_path: Path):
    """Test tracked file count metric with directory and pattern filter."""
    import subprocess

    # Create repo with multiple files in subdirectories
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create dags directory with python files
    dags_dir = repo_path / "dags"
    dags_dir.mkdir()
    (dags_dir / "dag1.py").write_text("# dag 1")
    (dags_dir / "dag2.py").write_text("# dag 2")
    (dags_dir / "config.yaml").write_text("config: true")

    # Create other files
    (repo_path / "README.md").write_text("# Test")

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Test filtering by directory and pattern
    result = (
        CheckHub()
        .with_metrics([DagCountMetric])
        .with_providers([[GitProvider(repo_path=repo_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dag_count"
    assert metric.value == 2  # Only dag1.py and dag2.py


class ReadmeExistsMetric(GitTrackedFileCountMetric):
    name = "readme_exists"
    description = "Whether README.md exists"
    pattern: str = "README.md"


def test_file_exists_metric_when_file_exists(git_repo: Path):
    """Test file exists metric returns True when file exists."""
    result = (
        CheckHub()
        .with_metrics([ReadmeExistsMetric])
        .with_providers([[GitProvider(repo_path=git_repo)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "readme_exists"
    assert metric.value == 1


class CruftFileExistsMetric(GitTrackedFileCountMetric):
    name = "cruft_file_exists"
    description = "Whether .cruft.json exists"
    pattern: str = ".cruft.json"


def test_tracked_file_count_when_no_match(git_repo: Path):
    """Test tracked file count returns 0 when pattern doesn't match."""
    result = (
        CheckHub()
        .with_metrics([CruftFileExistsMetric])
        .with_providers([[GitProvider(repo_path=git_repo)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "cruft_file_exists"
    assert metric.value == 0


def test_provider_returns_last_commit_date(git_repo: Path):
    """Test that provider returns last commit date."""
    provider = GitProvider(repo_path=git_repo)
    context = provider.provide()

    assert "git_last_commit_date" in context
    assert context["git_last_commit_date"] is not None


def test_provider_with_no_commits(tmp_path: Path):
    """Test provider with empty repo (no commits)."""
    import subprocess

    repo_path = tmp_path / "empty_repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

    provider = GitProvider(repo_path=repo_path)
    context = provider.provide()

    assert context["git_last_commit_date"] is None


def test_provider_with_monorepo_subdirectory(tmp_path: Path):
    """Test provider works correctly with a subdirectory in a monorepo."""
    import subprocess
    import time

    repo_path = tmp_path / "monorepo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create two subdirectories (projects in monorepo)
    project_a = repo_path / "project_a"
    project_b = repo_path / "project_b"
    project_a.mkdir()
    project_b.mkdir()

    # Commit to project_a first
    (project_a / "file.txt").write_text("project a content")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add project A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Wait a bit to ensure different timestamps
    time.sleep(1)

    # Commit to project_b later
    (project_b / "file.txt").write_text("project b content")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add project B"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Provider for project_a should return the older date
    provider_a = GitProvider(repo_path=project_a)
    context_a = provider_a.provide()

    # Provider for project_b should return the newer date
    provider_b = GitProvider(repo_path=project_b)
    context_b = provider_b.provide()

    # project_b was committed later, so its date should be more recent
    assert context_a["git_last_commit_date"] < context_b["git_last_commit_date"]
