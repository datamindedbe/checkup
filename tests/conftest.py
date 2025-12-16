"""Pytest configuration and shared fixtures."""

from typing import Any, ClassVar

import pytest

from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context


class DummyMetric(Metric):
    """Simple test metric with no dependencies.

    Always returns the expected_value from config.
    Used for testing the framework.
    """

    name: ClassVar[str] = "dummy"
    description: ClassVar[str] = "Test metric"
    unit: ClassVar[str] = "count"

    expected_value: int = 42

    def calculate(self, context: Context, metrics: dict) -> None:
        """Set value to expected_value."""
        self.value = self.expected_value
        self.diagnostic = (
            f"Dummy metric calculated with expected_value={self.expected_value}"
        )


class DependentDummyMetric(Metric):
    """Test metric that depends on DummyMetric.

    Doubles the value of DummyMetric.
    Used for testing dependency resolution.
    """

    name: ClassVar[str] = "dependent_dummy"
    description: ClassVar[str] = "Depends on DummyMetric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        """Depends on DummyMetric."""
        return [DummyMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        """Double the DummyMetric value."""
        base_value = metrics[DummyMetric].value
        self.value = base_value * 2
        self.diagnostic = f"Doubled DummyMetric value from {base_value} to {self.value}"


class Level2Metric(Metric):
    """Test metric at depth 2 in dependency chain."""

    name: ClassVar[str] = "level2"
    description: ClassVar[str] = "Depth 2 metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DependentDummyMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[DependentDummyMetric].value + 10
        self.diagnostic = f"Added 10 to DependentDummyMetric value: {self.value}"


class Level3Metric(Metric):
    """Test metric at depth 3 in dependency chain."""

    name: ClassVar[str] = "level3"
    description: ClassVar[str] = "Depth 3 metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [Level2Metric]

    def calculate(self, context: Context, metrics: dict) -> None:
        level2_value = metrics[Level2Metric].value
        self.value = level2_value**2
        self.diagnostic = f"Squared Level2Metric value: {level2_value}^2 = {self.value}"


class CyclicMetricA(Metric):
    """Test metric that creates a cycle with CyclicMetricB."""

    name: ClassVar[str] = "cyclic_a"
    description: ClassVar[str] = "Cyclic test metric A"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricB]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1
        self.diagnostic = "CyclicMetricA calculated"


class CyclicMetricB(Metric):
    """Test metric that creates a cycle with CyclicMetricA."""

    name: ClassVar[str] = "cyclic_b"
    description: ClassVar[str] = "Cyclic test metric B"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricA]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1
        self.diagnostic = "CyclicMetricB calculated"


# Complex Dependency Graph:
#
#   Subgraph 1:                       Subgraph 2:
#
#        RootA     RootB                   RootC
#          \       /   \                     |
#           \     /     \                    |
#          SharedAB    BranchB             LeafC
#              |          |
#              |          |
#          MidShared   MidBranch
#               \       /
#                \     /
#                LeafAB


class RootA(Metric):
    """Root metric A - no dependencies."""

    name: ClassVar[str] = "root_a"
    description: ClassVar[str] = "Root A metric"
    unit: ClassVar[str] = "count"
    base_value: int = 10

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = self.base_value
        self.diagnostic = f"RootA calculated with base_value={self.base_value}"


class RootB(Metric):
    """Root metric B - no dependencies."""

    name: ClassVar[str] = "root_b"
    description: ClassVar[str] = "Root B metric"
    unit: ClassVar[str] = "count"
    base_value: int = 20

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = self.base_value
        self.diagnostic = f"RootB calculated with base_value={self.base_value}"


class RootC(Metric):
    """Root metric C - no dependencies (independent subgraph)."""

    name: ClassVar[str] = "root_c"
    description: ClassVar[str] = "Root C metric"
    unit: ClassVar[str] = "count"
    base_value: int = 100

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = self.base_value
        self.diagnostic = f"RootC calculated with base_value={self.base_value}"


class SharedAB(Metric):
    """Metric with shared ancestors - depends on both RootA and RootB."""

    name: ClassVar[str] = "shared_ab"
    description: ClassVar[str] = "Shared AB metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootA, RootB]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Sum of both roots
        root_a_val = metrics[RootA].value
        root_b_val = metrics[RootB].value
        self.value = root_a_val + root_b_val
        self.diagnostic = (
            f"Sum of RootA ({root_a_val}) and RootB ({root_b_val}) = {self.value}"
        )


class BranchB(Metric):
    """Branch from RootB only."""

    name: ClassVar[str] = "branch_b"
    description: ClassVar[str] = "Branch B metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootB]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Triple the RootB value
        root_b_val = metrics[RootB].value
        self.value = root_b_val * 3
        self.diagnostic = f"Tripled RootB value: {root_b_val} * 3 = {self.value}"


class LeafC(Metric):
    """Leaf in independent subgraph - depends on RootC."""

    name: ClassVar[str] = "leaf_c"
    description: ClassVar[str] = "Leaf C metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootC]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Square root C
        root_c_val = metrics[RootC].value
        self.value = root_c_val**2
        self.diagnostic = f"Squared RootC value: {root_c_val}^2 = {self.value}"


class MidShared(Metric):
    """Middle layer - depends on SharedAB."""

    name: ClassVar[str] = "mid_shared"
    description: ClassVar[str] = "Mid shared metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [SharedAB]

    def calculate(self, context: Context, metrics: dict) -> None:
        shared_ab_val = metrics[SharedAB].value
        self.value = shared_ab_val + 5
        self.diagnostic = (
            f"Added 5 to SharedAB value: {shared_ab_val} + 5 = {self.value}"
        )


class MidBranch(Metric):
    """Middle layer - depends on BranchB."""

    name: ClassVar[str] = "mid_branch"
    description: ClassVar[str] = "Mid branch metric"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BranchB]

    def calculate(self, context: Context, metrics: dict) -> None:
        branch_b_val = metrics[BranchB].value
        self.value = branch_b_val * 2
        self.diagnostic = f"Doubled BranchB value: {branch_b_val} * 2 = {self.value}"


class LeafAB(Metric):
    """Leaf with diamond pattern - depends on both MidShared and MidBranch."""

    name: ClassVar[str] = "leaf_ab"
    description: ClassVar[str] = "Leaf AB metric (diamond convergence)"
    unit: ClassVar[str] = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [MidShared, MidBranch]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Product of both mid-level metrics
        mid_shared_val = metrics[MidShared].value
        mid_branch_val = metrics[MidBranch].value
        self.value = mid_shared_val * mid_branch_val
        self.diagnostic = f"Product of MidShared ({mid_shared_val}) and MidBranch ({mid_branch_val}) = {self.value}"


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

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context[DummyProvider.name]["data"]
        self.diagnostic = f"Retrieved dummy_data from context: {self.value}"


class FailingMetric(Metric):
    """Test metric that fails based on context."""

    name: ClassVar[str] = "failing"
    description: ClassVar[str] = "Fails when should_fail is True"
    unit: ClassVar[str] = "count"

    def calculate(self, context: Context, metrics: dict) -> None:
        if context.get("should_fail"):
            self.diagnostic = "Metric failed as requested by context"
            raise ValueError("Intentional failure")
        self.value = 1
        self.diagnostic = "Metric calculated successfully"


# Integration test metrics (must be at module level for ProcessPoolExecutor)


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

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context[IntegrationProvider.name]["base_value"]
        self.diagnostic = (
            f"Retrieved base_value from integration provider: {self.value}"
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

    def calculate(self, context: Context, metrics: dict) -> None:
        base_val = metrics[IntegrationBaseMetric].value
        self.value = base_val * self.multiplier
        self.diagnostic = f"Multiplied base metric value: {base_val} * {self.multiplier} = {self.value}"


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

    def calculate(self, context: Context, metrics: dict) -> None:
        path_len = context[PathLengthProvider.name]["length"]
        self.value = path_len * self.multiplier
        self.diagnostic = (
            f"Path length {path_len} * multiplier {self.multiplier} = {self.value}"
        )


class OtherDummyMetric(Metric):
    """Another test metric with a different name.

    Used for testing multiple metrics.
    """

    name: ClassVar[str] = "other_metric"
    description: ClassVar[str] = "Other test metric"
    unit: ClassVar[str] = "count"

    expected_value: int = 100

    def calculate(self, context: Context, metrics: dict) -> None:
        """Set value to expected_value."""
        self.value = self.expected_value
        self.diagnostic = (
            f"Other metric calculated with expected_value={self.expected_value}"
        )


class IndirectDummyMetric(Metric):
    """Test metric for testing indirect metric filtering.

    Used for testing materializer filtering.
    """

    name: ClassVar[str] = "indirect"
    description: ClassVar[str] = "Indirect test metric"
    unit: ClassVar[str] = "count"

    expected_value: int = 100

    def calculate(self, context: Context, metrics: dict) -> None:
        """Set value to expected_value."""
        self.value = self.expected_value
        self.diagnostic = (
            f"Indirect metric calculated with expected_value={self.expected_value}"
        )


@pytest.fixture
def dummy_metric():
    """Create a DummyMetric instance with default value."""
    return DummyMetric()


@pytest.fixture
def dummy_metric_with_value():
    """Create a DummyMetric instance with value already calculated."""
    metric = DummyMetric(expected_value=10)
    metric.calculate(context={}, metrics={})
    return metric


@pytest.fixture
def dependent_metric():
    """Create a DependentDummyMetric instance."""
    return DependentDummyMetric()


@pytest.fixture
def empty_context():
    """Create an empty context dict."""
    return {}
