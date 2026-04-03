"""Git metrics for checkup."""

from datetime import UTC, datetime
from fnmatch import fnmatch
from typing import ClassVar

from checkup.metric import Measurement, Metric
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

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        git_context = self.get_context(context)
        last_commit_date = git_context.get("git_last_commit_date")

        if not isinstance(last_commit_date, datetime):
            return self.measurement(value=None, diagnostic="No commits found")

        now = datetime.now(UTC)
        delta = now - last_commit_date
        return self.measurement(
            value=delta.days,
            diagnostic=f"Last commit: {last_commit_date.strftime('%Y-%m-%d')}",
        )


class GitTrackedFileCountMetric(GitMetric):
    """Number of git tracked files, optionally filtered by a glob pattern.

    Without configuration, counts all tracked files. Can be filtered by
    specifying a glob pattern that matches the full file path.

    Configure via subclassing.

    Example:
        class PythonTestFileCountMetric(GitTrackedFileCountMetric):
            name = "python_test_file_count"
            description = "Number of Python test files"
            pattern: str = "tests/test_*.py"
    """

    name: ClassVar[str] = "git_tracked_file_count"
    description: ClassVar[str] = "Number of git tracked files"
    unit: ClassVar[str] = "files"

    pattern: str = "*"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        git_context = self.get_context(context)
        tracked_files = git_context.get("git_tracked_files", [])

        if not isinstance(tracked_files, list):
            return self.measurement(value=0, diagnostic="No git repository found")

        if self.pattern != "*":
            matched_files = [f for f in tracked_files if fnmatch(f, self.pattern)]
            if matched_files:
                return self.measurement(
                    value=len(matched_files),
                    diagnostic=f"Matched files: {', '.join(matched_files)}",
                )
            else:
                return self.measurement(
                    value=len(matched_files),
                    diagnostic=f"No files matching pattern: {self.pattern}",
                )
        else:
            return self.measurement(value=len(tracked_files))
