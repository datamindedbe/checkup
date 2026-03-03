"""Git metrics for checkup."""

from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context
from checkup_git.provider import GitProvider


class GitMetric(Metric):
    """Base class for git-related metrics."""

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [GitProvider]

    def get_context(self, context: Context) -> dict:
        """Get the git context from the main context."""
        return context.get(GitProvider.name, {})


class GitDaysSinceLastUpdateMetric(GitMetric):
    """Number of days since the last git commit."""

    name: ClassVar[str] = "git_days_since_last_update"
    description: ClassVar[str] = "Days since the last git commit"
    unit: ClassVar[str] = "days"

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        git_context = self.get_context(context)
        last_commit_date = git_context.get("git_last_commit_date")

        if not isinstance(last_commit_date, datetime):
            self.value = None
            self.diagnostic = "No commits found"
            return

        now = datetime.now(UTC)
        delta = now - last_commit_date
        self.value = delta.days


class GitTrackedFileCountMetric(GitMetric):
    """Number of git tracked files in the repository path."""

    name: ClassVar[str] = "git_tracked_file_count"
    description: ClassVar[str] = "Number of git tracked files"
    unit: ClassVar[str] = "files"

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        git_context = self.get_context(context)
        self.value = git_context.get("git_tracked_file_count", 0)


class GitFileExistsMetric(GitMetric):
    """Metric that checks if a specific file exists.

    Configure via subclassing.

    Example:
        class ReadmeExistsMetric(GitFileExistsMetric):
            name = "readme_exists"
            description = "Whether README.md exists"
            file_path: str = "README.md"
    """

    name: ClassVar[str] = "git_file_exists"
    description: ClassVar[str] = "Whether a specific file exists"
    unit: ClassVar[str] = "boolean"

    file_path: str

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        git_context = self.get_context(context)
        repo_path = git_context.get("git_repo_path")

        if not isinstance(repo_path, Path):
            self.value = 0
            self.diagnostic = "No repository path found"
            return

        full_path = repo_path / self.file_path
        self.value = 1 if full_path.exists() else 0
