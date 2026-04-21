from typing import Any, ClassVar

from checkup.metric import Measurement, Metric
from checkup.provider import Provider
from checkup.types import Context


class DummyMetric(Metric):
    """Simple test metric with no dependencies."""

    name: ClassVar[str] = "dummy"
    description: ClassVar[str] = "Test metric"
    unit: ClassVar[str] = "count"

    expected_value: int = 42

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        """Set value to expected_value."""
        return self.measure(
            value=self.expected_value,
            diagnostic=f"Dummy metric calculated with expected_value={self.expected_value}",
        )


class DependentDummyMetric(Metric):
    """Test metric that depends on DummyMetric."""

    name: ClassVar[str] = "dependent_dummy"
    description: ClassVar[str] = "Depends on DummyMetric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        """Depends on DummyMetric."""
        return [DummyMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        """Double the DummyMetric value."""
        base_value = measurements[DummyMetric].value
        value = base_value * 2
        return self.measure(
            value=value,
            diagnostic=f"Doubled DummyMetric value from {base_value} to {value}",
        )


class Level2Metric(Metric):
    """Test metric at depth 2 in dependency chain."""

    name: ClassVar[str] = "level2"
    description: ClassVar[str] = "Depth 2 metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DependentDummyMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        value = measurements[DependentDummyMetric].value + 10
        return self.measure(
            value=value, diagnostic=f"Added 10 to DependentDummyMetric value: {value}"
        )


class Level3Metric(Metric):
    """Test metric at depth 3 in dependency chain."""

    name: ClassVar[str] = "level3"
    description: ClassVar[str] = "Depth 3 metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [Level2Metric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        level2_value = measurements[Level2Metric].value
        value = level2_value**2
        return self.measure(
            value=value,
            diagnostic=f"Squared Level2Metric value: {level2_value}^2 = {value}",
        )


class CyclicMetricA(Metric):
    """Test metric that creates a cycle with CyclicMetricB."""

    name: ClassVar[str] = "cyclic_a"
    description: ClassVar[str] = "Cyclic test metric A"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricB]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        return self.measure(value=1, diagnostic="CyclicMetricA calculated")


class CyclicMetricB(Metric):
    """Test metric that creates a cycle with CyclicMetricA."""

    name: ClassVar[str] = "cyclic_b"
    description: ClassVar[str] = "Cyclic test metric B"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricA]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        return self.measure(value=1, diagnostic="CyclicMetricB calculated")


class RootA(Metric):
    """Root metric A - no dependencies."""

    name: ClassVar[str] = "root_a"
    description: ClassVar[str] = "Root A metric"
    unit: ClassVar[str] = "count"
    base_value: int = 10

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        return self.measure(
            value=self.base_value,
            diagnostic=f"RootA calculated with base_value={self.base_value}",
        )


class RootB(Metric):
    """Root metric B - no dependencies."""

    name: ClassVar[str] = "root_b"
    description: ClassVar[str] = "Root B metric"
    unit: ClassVar[str] = "count"
    base_value: int = 20

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        return self.measure(
            value=self.base_value,
            diagnostic=f"RootB calculated with base_value={self.base_value}",
        )


class RootC(Metric):
    """Root metric C - no dependencies (independent subgraph)."""

    name: ClassVar[str] = "root_c"
    description: ClassVar[str] = "Root C metric"
    unit: ClassVar[str] = "count"
    base_value: int = 100

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        return self.measure(
            value=self.base_value,
            diagnostic=f"RootC calculated with base_value={self.base_value}",
        )


class SharedAB(Metric):
    """Metric with shared ancestors - depends on both RootA and RootB."""

    name: ClassVar[str] = "shared_ab"
    description: ClassVar[str] = "Shared AB metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootA, RootB]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        root_a_val = measurements[RootA].value
        root_b_val = measurements[RootB].value
        value = root_a_val + root_b_val
        return self.measure(
            value=value,
            diagnostic=f"Sum of RootA ({root_a_val}) and RootB ({root_b_val}) = {value}",
        )


class BranchB(Metric):
    """Branch from RootB only."""

    name: ClassVar[str] = "branch_b"
    description: ClassVar[str] = "Branch B metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootB]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        root_b_val = measurements[RootB].value
        value = root_b_val * 3
        return self.measure(
            value=value, diagnostic=f"Tripled RootB value: {root_b_val} * 3 = {value}"
        )


class LeafC(Metric):
    """Leaf in independent subgraph - depends on RootC."""

    name: ClassVar[str] = "leaf_c"
    description: ClassVar[str] = "Leaf C metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootC]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        root_c_val = measurements[RootC].value
        value = root_c_val**2
        return self.measure(
            value=value, diagnostic=f"Squared RootC value: {root_c_val}^2 = {value}"
        )


class MidShared(Metric):
    """Middle layer - depends on SharedAB."""

    name: ClassVar[str] = "mid_shared"
    description: ClassVar[str] = "Mid shared metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [SharedAB]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        shared_ab_val = measurements[SharedAB].value
        value = shared_ab_val + 5
        return self.measure(
            value=value,
            diagnostic=f"Added 5 to SharedAB value: {shared_ab_val} + 5 = {value}",
        )


class MidBranch(Metric):
    """Middle layer - depends on BranchB."""

    name: ClassVar[str] = "mid_branch"
    description: ClassVar[str] = "Mid branch metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BranchB]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        branch_b_val = measurements[BranchB].value
        value = branch_b_val * 2
        return self.measure(
            value=value,
            diagnostic=f"Doubled BranchB value: {branch_b_val} * 2 = {value}",
        )


class LeafAB(Metric):
    """Leaf with diamond pattern - depends on both MidShared and MidBranch."""

    name: ClassVar[str] = "leaf_ab"
    description: ClassVar[str] = "Leaf AB metric (diamond convergence)"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [MidShared, MidBranch]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        mid_shared_val = measurements[MidShared].value
        mid_branch_val = measurements[MidBranch].value
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

    name: ClassVar[str] = "provider_dummy"
    description: ClassVar[str] = "Uses dummy provider"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DummyProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        value = context[DummyProvider.name]["data"]
        return self.measure(
            value=value, diagnostic=f"Retrieved dummy_data from context: {value}"
        )


class FailingMetric(Metric):
    """Test metric that fails based on context."""

    name: ClassVar[str] = "failing"
    description: ClassVar[str] = "Fails when should_fail is True"
    unit: ClassVar[str] = "count"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
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

    name: ClassVar[str] = "base_metric"
    description: ClassVar[str] = "Base test metric"
    unit: ClassVar[str] = "units"
    threshold: int = 100

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [IntegrationProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        value = context[IntegrationProvider.name]["base_value"]
        return self.measure(
            value=value,
            diagnostic=f"Retrieved base_value from integration provider: {value}",
        )


class IntegrationDerivedMetric(Metric):
    """Derived metric for integration tests."""

    name: ClassVar[str] = "derived_metric"
    description: ClassVar[str] = "Derived test metric"
    unit: ClassVar[str] = "units"
    multiplier: int = 2

    @classmethod
    def depends_on(cls):
        return [IntegrationBaseMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        base_val = measurements[IntegrationBaseMetric].value
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

    name: ClassVar[str] = "path_metric"
    description: ClassVar[str] = "Calculates based on path"
    unit: ClassVar[str] = "count"
    multiplier: int = 1

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [PathLengthProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        path_len = context[PathLengthProvider.name]["length"]
        value = path_len * self.multiplier
        return self.measure(
            value=value,
            diagnostic=f"Path length {path_len} * multiplier {self.multiplier} = {value}",
        )


class OtherDummyMetric(Metric):
    """Another test metric with a different name."""

    name: ClassVar[str] = "other_metric"
    description: ClassVar[str] = "Other test metric"
    unit: ClassVar[str] = "count"

    expected_value: int = 100

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        """Set value to expected_value."""
        return self.measure(
            value=self.expected_value,
            diagnostic=f"Other metric calculated with expected_value={self.expected_value}",
        )


class IndirectDummyMetric(Metric):
    """Test metric for testing indirect metric filtering."""

    name: ClassVar[str] = "indirect"
    description: ClassVar[str] = "Indirect test metric"
    unit: ClassVar[str] = "count"

    expected_value: int = 100

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        """Set value to expected_value."""
        return self.measure(
            value=self.expected_value,
            diagnostic=f"Indirect metric calculated with expected_value={self.expected_value}",
        )
