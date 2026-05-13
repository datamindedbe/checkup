"""
Configuration models.
"""

from typing import Any

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""

    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class MetricConfig(BaseModel):
    type: str
    name: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    @property
    def instance_name(self) -> str:
        return self.name or self.type


class MaterializerConfig(BaseModel):
    """Configuration for the materializer."""

    type: str
    config: dict[str, Any] = Field(default_factory=dict)


class CheckupConfig(BaseModel):
    """Complete checkup configuration."""

    tags: dict[str, Any] = Field(default_factory=dict)
    providers: list[ProviderConfig] = Field(default_factory=list)
    metrics: list[MetricConfig] = Field(default_factory=list)
    materializer: MaterializerConfig | None = None

    @classmethod
    def empty(cls) -> "CheckupConfig":
        return cls()
