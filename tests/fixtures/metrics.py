from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.types import Context


class DummyMetric(Metric):
    """Simple test metric with no dependencies."""

    name: str = "dummy"
    description: str = "Test metric"
    unit: str = "count"

    expected_value: int = 42

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        """Set value to expected_value."""
        return self.measure(
            value=self.expected_value,
            diagnostic=f"Dummy metric calculated with expected_value={self.expected_value}",
        )


class OtherDummyMetric(Metric):
    """Another test metric with a different name."""

    name: str = "other_metric"
    description: str = "Other test metric"
    unit: str = "count"

    expected_value: int = 100

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        """Set value to expected_value."""
        return self.measure(
            value=self.expected_value,
            diagnostic=f"Other metric calculated with expected_value={self.expected_value}",
        )


class IndirectDummyMetric(Metric):
    """Test metric for testing indirect metric filtering."""

    name: str = "indirect"
    description: str = "Indirect test metric"
    unit: str = "count"

    expected_value: int = 100

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        """Set value to expected_value."""
        return self.measure(
            value=self.expected_value,
            diagnostic=f"Indirect metric calculated with expected_value={self.expected_value}",
        )


class DependentDummyMetric(Metric):
    """Test metric that depends on DummyMetric."""

    name: str = "dependent_dummy"
    description: str = "Depends on DummyMetric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        """Depends on DummyMetric."""
        return [DummyMetric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        """Double the DummyMetric value."""
        base_value = measurements.get(DummyMetric).value
        value = base_value * 2
        return self.measure(
            value=value,
            diagnostic=f"Doubled DummyMetric value from {base_value} to {value}",
        )


class Level2Metric(Metric):
    """Test metric at depth 2 in dependency chain."""

    name: str = "level2"
    description: str = "Depth 2 metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DependentDummyMetric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        value = measurements.get(DependentDummyMetric).value + 10
        return self.measure(
            value=value, diagnostic=f"Added 10 to DependentDummyMetric value: {value}"
        )


class Level3Metric(Metric):
    """Test metric at depth 3 in dependency chain."""

    name: str = "level3"
    description: str = "Depth 3 metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [Level2Metric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        level2_value = measurements.get(Level2Metric).value
        value = level2_value**2
        return self.measure(
            value=value,
            diagnostic=f"Squared Level2Metric value: {level2_value}^2 = {value}",
        )


class CyclicMetricA(Metric):
    """Test metric that creates a cycle with CyclicMetricB."""

    name: str = "cyclic_a"
    description: str = "Cyclic test metric A"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricB]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        return self.measure(value=1, diagnostic="CyclicMetricA calculated")


class CyclicMetricB(Metric):
    """Test metric that creates a cycle with CyclicMetricA."""

    name: str = "cyclic_b"
    description: str = "Cyclic test metric B"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricA]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        return self.measure(value=1, diagnostic="CyclicMetricB calculated")


class FailingMetric(Metric):
    """Test metric that fails based on context."""

    name: str = "failing"
    description: str = "Fails when should_fail is True"
    unit: str = "count"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        if context.get("should_fail"):
            raise ValueError("Intentional failure")
        return self.measure(value=1, diagnostic="Metric calculated successfully")
