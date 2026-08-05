import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)

CRUFT_FILE = ".cruft.json"


class CruftProvider(Provider):
    """
    Provides cruft template context.

    With fetch_template=True it also clones the template to measure drift.
    """

    name: ClassVar[str] = "cruft"

    def __init__(self, project_path: str | Path = ".", fetch_template: bool = False):
        self.project_path = Path(project_path)
        self.fetch_template = fetch_template

    def provide(self) -> dict[str, Any]:
        cruft_path = self.project_path / CRUFT_FILE
        if not cruft_path.exists():
            return {"present": False}

        config = json.loads(cruft_path.read_text())
        template = config.get("template")
        commit = config.get("commit")

        context: dict[str, Any] = {
            "present": True,
            "template": template,
            "commit": commit,
            "directory": config.get("directory"),
            "last_update_date": self._last_update_date(),
            "conflict_files": self._conflict_files(),
        }

        if self.fetch_template and template and commit:
            context.update(
                self._template_drift(template, commit, config.get("checkout"))
            )

        return context

    def _last_update_date(self) -> datetime | None:
        """
        Author date of the most recent commit touching .cruft.json.
        """

        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", CRUFT_FILE],
            cwd=self.project_path,
            capture_output=True,
            text=True,
        )
        date_str = result.stdout.strip()
        return datetime.fromisoformat(date_str) if date_str else None

    def _conflict_files(self) -> list[str]:
        """
        Reject files a failed `cruft update` leaves behind.
        """

        result = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z", "--", "*.rej"],
            cwd=self.project_path,
            capture_output=True,
            text=True,
        )
        return [f for f in result.stdout.split("\0") if f]

    def _template_drift(
        self,
        template: str,
        pinned: str,
        checkout: str | None,
    ) -> dict[str, Any]:
        """
        Clone the template and measure how far the pinned commit lags its head.
        """

        try:
            with tempfile.TemporaryDirectory() as tmp:
                subprocess.run(
                    ["git", "clone", "--quiet", template, tmp],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                head = self._git(tmp, "rev-parse", checkout or "HEAD")
                behind = int(self._git(tmp, "rev-list", "--count", f"{pinned}..{head}"))

                return {
                    "template_head": head,
                    "commits_behind": behind,
                    "pinned_date": self._commit_date(tmp, pinned),
                    "head_date": self._commit_date(tmp, head),
                }
        except (subprocess.CalledProcessError, ValueError) as exc:
            logger.warning(f"Could not fetch cruft template {template}: {exc}")
            return {}

    def _commit_date(self, repo: str, ref: str) -> datetime | None:
        try:
            return datetime.fromisoformat(
                self._git(repo, "show", "-s", "--format=%cI", ref)
            )
        except (subprocess.CalledProcessError, ValueError):
            return None

    @staticmethod
    def _git(repo: str, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", repo, *args], check=True, capture_output=True, text=True
        )
        return result.stdout.strip()
