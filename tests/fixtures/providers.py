from typing import Any, ClassVar

from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context


class DummyProvider(Provider):
    """Test provider that adds dummy data to context."""

    name: ClassVar[str] = "dummy"

    def __init__(self, data: int = 100):
        self.data = data

    def provide(self) -> dict[str, Any]:
        return {"data": self.data}


class ProviderDummyMetric(Metric):
    """Test metric that uses a provider."""

    name: str = "provider_dummy"
    description: str = "Uses dummy provider"
    unit: str = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DummyProvider]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        value = context[DummyProvider.name]["data"]
        return self.measure(
            value=value, diagnostic=f"Retrieved dummy_data from context: {value}"
        )


class IntegrationProvider(Provider):
    """Provider that adds base_value to context."""

    name: ClassVar[str] = "integration"

    def __init__(self, base_value: int = 25):
        self.base_value = base_value

    def provide(self) -> dict[str, Any]:
        return {"base_value": self.base_value}


class IntegrationBaseMetric(Metric):
    """Base metric for integration tests."""

    name: str = "base_metric"
    description: str = "Base test metric"
    unit: str = "units"
    threshold: int = 100

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [IntegrationProvider]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        value = context[IntegrationProvider.name]["base_value"]
        return self.measure(
            value=value,
            diagnostic=f"Retrieved base_value from integration provider: {value}",
        )


class IntegrationDerivedMetric(Metric):
    """Derived metric for integration tests."""

    name: str = "derived_metric"
    description: str = "Derived test metric"
    unit: str = "units"
    multiplier: int = 2

    @classmethod
    def depends_on(cls):
        return [IntegrationBaseMetric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        base_val = measurements.get(IntegrationBaseMetric).value
        value = base_val * self.multiplier
        return self.measure(
            value=value,
            diagnostic=f"Multiplied base metric value: {base_val} * {self.multiplier} = {value}",
        )


class PathLengthProvider(Provider):
    """Provider that calculates path length."""

    name: ClassVar[str] = "path_length"

    def __init__(self, path: str = "/unknown"):
        self.path = path

    def provide(self) -> dict[str, Any]:
        return {"length": len(self.path)}


class PathMetric(Metric):
    """Metric that uses path length from context."""

    name: str = "path_metric"
    description: str = "Calculates based on path"
    unit: str = "count"
    multiplier: int = 1

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [PathLengthProvider]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        path_len = context[PathLengthProvider.name]["length"]
        value = path_len * self.multiplier
        return self.measure(
            value=value,
            diagnostic=f"Path length {path_len} * multiplier {self.multiplier} = {value}",
        )
