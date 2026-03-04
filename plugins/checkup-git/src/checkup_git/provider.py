"""Git repository provider for checkup."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class GitProvider(Provider):
    """Provides git repository context.

    Extracts metadata from a git repository including last commit date.

    Example:
        GitProvider(repo_path="./my_repo")
    """

    name: ClassVar[str] = "git"

    def __init__(self, repo_path: str | Path = "."):
        """Initialize GitProvider.

        Args:
            repo_path: Path to git repository. Defaults to current directory.
        """
        self.repo_path = Path(repo_path)

    def provide(self) -> dict[str, Any]:
        """Get git repository information.

        Returns:
            Dict with git metadata.
        """
        logger.info(f"Getting git info from {self.repo_path}")

        if not self.repo_path.exists():
            logger.warning(f"Path does not exist: {self.repo_path}")
            return {
                "git_repo_path": self.repo_path,
                "git_last_commit_date": None,
                "git_tracked_files": [],
            }

        tracked_files = self._get_tracked_files()
        last_commit_date = self._get_last_commit_date(tracked_files)

        return {
            "git_repo_path": self.repo_path,
            "git_last_commit_date": last_commit_date,
            "git_tracked_files": tracked_files,
        }

    def _get_last_commit_date(self, git_files: list[str]) -> datetime | None:
        """Get the date of the most recent commit to any tracked file."""
        if not git_files:
            return None

        last_commit_dates = [
            date
            for file in git_files
            if (date := self._get_file_last_commit_date(file)) is not None
        ]

        return max(last_commit_dates) if last_commit_dates else None

    def _get_tracked_files(self) -> list[str]:
        """List all git tracked files in the repo path."""
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.warning(f"Failed to list git files: {result.stderr}")
            return []
        return result.stdout.splitlines()

    def _get_file_last_commit_date(self, file: str) -> datetime | None:
        """Get the last commit date for a specific file."""
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", file],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        date_str = result.stdout.strip()
        if not date_str:
            return None
        return datetime.fromisoformat(date_str)
