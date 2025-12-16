import json
import logging
import subprocess
from typing import Callable, ClassVar

from checkup.metric import Metric
from checkup.types import Context
from checkup_python.provider import PythonProvider

logger = logging.getLogger(__name__)


class PythonLinterMetric(Metric):
    """
    Base class for Python linter metrics.
    """

    name: ClassVar[str] = "python_linter"
    description: ClassVar[str] = ""
    unit: ClassVar[str] = ""

    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        return [PythonProvider]

    def calculate(
        self, context: Context, metrics: dict[type[Metric], Metric]
    ) -> None: ...

    def run_ruff(self, dir: str) -> dict:
        """
        Run ruff linter against the project.
        Uses uvx to run ruff temporarily without affecting the project's dependencies.
        """

        try:
            result = subprocess.run(
                ["uvx", "ruff", "check", ".", "--output-format=json"],
                cwd=dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            logger.warning("Ruff linting timed out after 2 minutes")
            return
        except FileNotFoundError:
            logger.warning("uvx command not found. Is uv installed?")
            return
        except Exception as e:
            logger.error(f"Error running ruff: {str(e)}")
            return


class PythonLinterWarningsMetric(PythonLinterMetric):
    name: ClassVar[str] = "python_linter_warnings"
    description: ClassVar[str] = (
        "Number of linting warnings detected by ruff (style and best practices)"
    )
    unit: ClassVar[str] = "warnings"

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        python_context = context[PythonProvider.name]
        output = self.run_ruff(python_context["dir"])

        if output is None:
            self.value = None
            self.diagnostic = "Ruff linting could not be performed."
            return

        # Count warnings: style and best practice issues (E, W, B, etc.) but not F or E9*
        warnings = [d for d in output if not self._is_error(d["code"])]
        self.value = len(warnings)
        self.diagnostic = f"Found {self.value} linting warnings"

    @staticmethod
    def _is_error(code: str) -> bool:
        """
        Determine if a diagnostic code represents an error (actual bug).
        Errors: F-series (Pyflakes), E9* (syntax errors)
        Warnings: Everything else (style, best practices)
        """
        return code.startswith("F") or code.startswith("E9")


class PythonLinterErrorsMetric(PythonLinterMetric):
    name: ClassVar[str] = "python_linter_errors"
    description: ClassVar[str] = (
        "Number of linting errors detected by ruff (actual bugs)"
    )
    unit: ClassVar[str] = "errors"

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        python_context = context[PythonProvider.name]
        output = self.run_ruff(python_context["dir"])

        if output is None:
            self.value = None
            self.diagnostic = "Ruff linting could not be performed."
            return

        # Count errors: F-series (Pyflakes) and E9* (syntax errors)
        errors = [
            d for d in output if d["code"].startswith("F") or d["code"].startswith("E9")
        ]
        self.value = len(errors)
        self.diagnostic = f"Found {self.value} linting errors"
