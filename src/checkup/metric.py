"""Metric base class."""

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar

from pydantic import BaseModel, Field

from checkup.types import Context


class Metric(ABC, BaseModel):
    """Base class for all metrics.

    Metrics are Pydantic models that calculate values from context.
    They can depend on other metrics and declare providers for context enrichment.
    """

    name: ClassVar[str]
    description: ClassVar[str]
    unit: ClassVar[str]

    tags: dict = Field(default_factory=dict)

    value: Any = None

    # Whether this metric was directly requested (vs auto-added as dependency)
    is_direct: bool = True

    @abstractmethod
    def calculate(
        self, context: Context, metrics: dict[type["Metric"], "Metric"]
    ) -> None:
        """Calculate metric value and set self.value.

        Args:
            context: General context enriched by providers
            metrics: Dict of already-calculated metric instances (dependencies)
        """
        pass

    @classmethod
    def depends_on(cls) -> list[type["Metric"]]:
        """Return list of metric classes this metric depends on.

        Returns:
            List of metric classes (empty by default)
        """
        return []

    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        """Return list of provider functions to enrich context.

        Returns:
            List of provider functions (empty by default)
        """
        return []
