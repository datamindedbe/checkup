import re
import sys
from pathlib import Path
from typing import Optional

from checkup.metric import Metric
from checkup.types import Context


class PythonVersionMetric(Metric):
    """
    Metric to detect the Python version configured for a project.

    Checks (in order):
    1. .python-version file
    2. pyproject.toml
    3. Falls back to current runtime version
    """

    name: str = "python_version"
    description: str = "The Python version configured for the project"
    unit: str = "version"

    def calculate(self, context: Context, metrics: dict) -> None:
        path = None

        if "path" in context:
            path = Path(context["path"])
        else:
            path = Path.cwd()

        version = (
            self._read_python_version_file(path)
            or self._read_pyproject_toml(path)
            or self._get_runtime_version()
        )

        self.value = version

    def _read_python_version_file(self, path: Path) -> Optional[str]:
        """
        Read version from `.python-version`.
        """

        version_file = path / ".python-version"
        if not version_file.exists():
            return None

        return (
            version_file.read_text().strip().removeprefix("python-").removeprefix("py")
        )

    def _read_pyproject_toml(self, path: Path) -> Optional[str]:
        """
        Extract Python version from `pyproject.toml`.
        """

        pyproject_file = path / "pyproject.toml"
        if not pyproject_file.exists():
            return None

        content = pyproject_file.read_text()
        # Look for requires-python = ">=3.11" or similar
        match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            return None

        version_spec = match.group(1)
        # Extract version number from spec like ">=3.11", "^3.11", "~=3.11.0"
        version_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_spec)
        if not version_match:
            return None

        return version_match.group(1)

    def _get_runtime_version(self) -> str:
        """
        Get the current runtime Python version.
        """

        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _parse_version(self, version: str) -> tuple[int, ...]:
        """
        Parse version string into tuple of integers for comparison.
        """

        parts = version.split(".")
        return tuple(int(part) for part in parts if part.isdigit())

    def __lt__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return self._parse_version(self.value) < self._parse_version(other.value)

    def __le__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return self._parse_version(self.value) <= self._parse_version(other.value)

    def __gt__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return self._parse_version(self.value) > self._parse_version(other.value)

    def __ge__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return self._parse_version(self.value) >= self._parse_version(other.value)

    def __eq__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return self._parse_version(self.value) == self._parse_version(other.value)

    def __ne__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return self._parse_version(self.value) != self._parse_version(other.value)
