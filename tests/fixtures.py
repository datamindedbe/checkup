from typing import Any, ClassVar

from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.provider import Provider
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


class RootA(Metric):
    """Root metric A - no dependencies."""

    name: str = "root_a"
    description: str = "Root A metric"
    unit: str = "count"
    base_value: int = 10

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        return self.measure(
            value=self.base_value,
            diagnostic=f"RootA calculated with base_value={self.base_value}",
        )


class RootB(Metric):
    """Root metric B - no dependencies."""

    name: str = "root_b"
    description: str = "Root B metric"
    unit: str = "count"
    base_value: int = 20

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        return self.measure(
            value=self.base_value,
            diagnostic=f"RootB calculated with base_value={self.base_value}",
        )


class RootC(Metric):
    """Root metric C - no dependencies (independent subgraph)."""

    name: str = "root_c"
    description: str = "Root C metric"
    unit: str = "count"
    base_value: int = 100

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        return self.measure(
            value=self.base_value,
            diagnostic=f"RootC calculated with base_value={self.base_value}",
        )


class SharedAB(Metric):
    """Metric with shared ancestors - depends on both RootA and RootB."""

    name: str = "shared_ab"
    description: str = "Shared AB metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootA, RootB]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        root_a_val = measurements.get(RootA).value
        root_b_val = measurements.get(RootB).value
        value = root_a_val + root_b_val
        return self.measure(
            value=value,
            diagnostic=f"Sum of RootA ({root_a_val}) and RootB ({root_b_val}) = {value}",
        )


class BranchB(Metric):
    """Branch from RootB only."""

    name: str = "branch_b"
    description: str = "Branch B metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootB]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        root_b_val = measurements.get(RootB).value
        value = root_b_val * 3
        return self.measure(
            value=value, diagnostic=f"Tripled RootB value: {root_b_val} * 3 = {value}"
        )


class LeafC(Metric):
    """Leaf in independent subgraph - depends on RootC."""

    name: str = "leaf_c"
    description: str = "Leaf C metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootC]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        root_c_val = measurements.get(RootC).value
        value = root_c_val**2
        return self.measure(
            value=value, diagnostic=f"Squared RootC value: {root_c_val}^2 = {value}"
        )


class MidShared(Metric):
    """Middle layer - depends on SharedAB."""

    name: str = "mid_shared"
    description: str = "Mid shared metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [SharedAB]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        shared_ab_val = measurements.get(SharedAB).value
        value = shared_ab_val + 5
        return self.measure(
            value=value,
            diagnostic=f"Added 5 to SharedAB value: {shared_ab_val} + 5 = {value}",
        )


class MidBranch(Metric):
    """Middle layer - depends on BranchB."""

    name: str = "mid_branch"
    description: str = "Mid branch metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BranchB]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        branch_b_val = measurements.get(BranchB).value
        value = branch_b_val * 2
        return self.measure(
            value=value,
            diagnostic=f"Doubled BranchB value: {branch_b_val} * 2 = {value}",
        )


class LeafAB(Metric):
    """Leaf with diamond pattern - depends on both MidShared and MidBranch."""

    name: str = "leaf_ab"
    description: str = "Leaf AB metric (diamond convergence)"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [MidShared, MidBranch]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        mid_shared_val = measurements.get(MidShared).value
        mid_branch_val = measurements.get(MidBranch).value
        value = mid_shared_val * mid_branch_val
        return self.measure(
            value=value,
            diagnostic=f"Product of MidShared ({mid_shared_val}) and MidBranch ({mid_branch_val}) = {value}",
        )


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


class FailingMetric(Metric):
    """Test metric that fails based on context."""

    name: str = "failing"
    description: str = "Fails when should_fail is True"
    unit: str = "count"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        if context.get("should_fail"):
            raise ValueError("Intentional failure")
        return self.measure(value=1, diagnostic="Metric calculated successfully")


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
