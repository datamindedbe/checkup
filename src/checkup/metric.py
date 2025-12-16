"""Metric base class."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from checkup.types import Context

if TYPE_CHECKING:
    from checkup.provider import Provider


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
    diagnostic: str = ""

    @abstractmethod
    def calculate(
        self, context: Context, metrics: dict[type["Metric"], "Metric"]
    ) -> None:
        """Calculate metric value and set self.value and self.diagnostic.

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
    def providers(cls) -> list[type["Provider"]]:
        """Return list of provider classes to enrich context.

        Returns:
            List of provider classes (empty by default)
        """
        return []
