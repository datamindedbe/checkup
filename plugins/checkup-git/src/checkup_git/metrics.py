"""Git metrics for checkup."""

from datetime import UTC, datetime
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
