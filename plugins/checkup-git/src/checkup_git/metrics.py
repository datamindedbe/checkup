"""Git metrics for checkup."""

from datetime import UTC, datetime
from fnmatch import fnmatch

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

    name: str = "git_days_since_last_update"
    description: str = "Days since the last git commit"
    unit: str = "days"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        git_context = self.get_context(context)
        last_commit_date = git_context.get("git_last_commit_date")

        if not isinstance(last_commit_date, datetime):
            return self.measure(value=None, diagnostic="No commits found")

        now = datetime.now(UTC)
        delta = now - last_commit_date
        return self.measure(
            value=delta.days,
            diagnostic=f"Last commit: {last_commit_date.strftime('%Y-%m-%d')}",
        )


class GitTrackedFileCountMetric(GitMetric):
    """Number of git tracked files, optionally filtered by a glob pattern.

    Without configuration, counts all tracked files. Can be filtered by
    specifying a glob pattern that matches the full file path.

    Configure via constructor or subclassing.

    Example:
        GitTrackedFileCountMetric(
            name="python_test_file_count",
            description="Number of Python test files",
            pattern="tests/test_*.py"
        )
    """

    name: str = "git_tracked_file_count"
    description: str = "Number of git tracked files"
    unit: str = "files"

    pattern: str = "*"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        git_context = self.get_context(context)
        tracked_files = git_context.get("git_tracked_files", [])

        if not isinstance(tracked_files, list):
            return self.measure(value=0, diagnostic="No git repository found")

        if self.pattern != "*":
            matched_files = [f for f in tracked_files if fnmatch(f, self.pattern)]
            if matched_files:
                return self.measure(
                    value=len(matched_files),
                    diagnostic=f"Matched files: {', '.join(matched_files)}",
                )
            else:
                return self.measure(
                    value=len(matched_files),
                    diagnostic=f"No files matching pattern: {self.pattern}",
                )
        else:
            return self.measure(value=len(tracked_files))
