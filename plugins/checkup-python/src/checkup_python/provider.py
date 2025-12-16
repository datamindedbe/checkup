import logging
import subprocess
from pathlib import Path
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class PythonProvider(Provider):
    name: ClassVar[str] = "python"

    dir: str

    def __init__(self, dir: str):
        self.dir = dir

    def provide(self) -> dict[str, Any]:
        context = {
            "installed": False,
            "dir": self.dir,
        }

        if not self._is_uv_project():
            return context

        context["installed"] = self._install_project()

        return context

    def _is_uv_project(self) -> bool:
        """
        Check if the directory is a uv project.
        """

        path = Path(self.dir)
        pyproject_path = path / "pyproject.toml"

        if not pyproject_path.exists():
            return False

        uv_lock_path = path / "uv.lock"
        if uv_lock_path.exists():
            return True

        try:
            with open(pyproject_path, "r") as f:
                content = f.read()
                return "[tool.uv]" in content
        except Exception:
            return False

    def _install_project(self) -> bool:
        """
        Install the project using uv.
        """

        try:
            result = subprocess.run(
                ["uv", "sync"],
                cwd=self.dir,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning("Installation timed out after 5 minutes")
            return False
        except FileNotFoundError:
            logger.warning("uv command not found. Is uv installed?")
            return False
        except Exception as e:
            logger.error(f"Error during installation: {str(e)}")
            return False
