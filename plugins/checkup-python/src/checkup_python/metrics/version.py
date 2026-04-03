import re
import sys
from pathlib import Path
from typing import ClassVar

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_python.metrics.utils import parse_semantic_version


class PythonVersionMetric(Metric):
    """
    Metric to detect the Python version configured for a project.

    Checks (in order):
    1. .python-version file
    2. pyproject.toml
    3. Falls back to current runtime version
    """

    name: ClassVar[str] = "python_version"
    description: ClassVar[str] = "The Python version configured for the project"
    unit: ClassVar[str] = "version"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
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

        return self.measurement(value=version)

    def _read_python_version_file(self, path: Path) -> str | None:
        """
        Read version from `.python-version`.
        """

        version_file = path / ".python-version"
        if not version_file.exists():
            return None

        return (
            version_file.read_text().strip().removeprefix("python-").removeprefix("py")
        )

    def _read_pyproject_toml(self, path: Path) -> str | None:
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

    def __lt__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return parse_semantic_version(self.value) < parse_semantic_version(other.value)

    def __le__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return parse_semantic_version(self.value) <= parse_semantic_version(other.value)

    def __gt__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return parse_semantic_version(self.value) > parse_semantic_version(other.value)

    def __ge__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return parse_semantic_version(self.value) >= parse_semantic_version(other.value)

    def __eq__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return parse_semantic_version(self.value) == parse_semantic_version(other.value)

    def __ne__(self, other) -> bool:
        if not isinstance(other, PythonVersionMetric):
            return NotImplemented
        return parse_semantic_version(self.value) != parse_semantic_version(other.value)
