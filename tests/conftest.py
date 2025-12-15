"""Pytest configuration and shared fixtures."""
import pytest

from checkup.metric import Metric
from checkup.types import Context


class DummyMetric(Metric):
    """Simple test metric with no dependencies.

    Always returns the expected_value from config.
    Used for testing the framework.
    """

    name: str = "dummy"
    description: str = "Test metric"
    unit: str = "count"

    expected_value: int = 42

    def calculate(self, context: Context, metrics: dict) -> None:
        """Set value to expected_value."""
        self.value = self.expected_value


class DependentDummyMetric(Metric):
    """Test metric that depends on DummyMetric.

    Doubles the value of DummyMetric.
    Used for testing dependency resolution.
    """

    name: str = "dependent_dummy"
    description: str = "Depends on DummyMetric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        """Depends on DummyMetric."""
        return [DummyMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        """Double the DummyMetric value."""
        base_value = metrics[DummyMetric].value
        self.value = base_value * 2


class Level2Metric(Metric):
    """Test metric at depth 2 in dependency chain."""

    name: str = "level2"
    description: str = "Depth 2 metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DependentDummyMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[DependentDummyMetric].value + 10


class Level3Metric(Metric):
    """Test metric at depth 3 in dependency chain."""

    name: str = "level3"
    description: str = "Depth 3 metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [Level2Metric]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[Level2Metric].value ** 2


class CyclicMetricA(Metric):
    """Test metric that creates a cycle with CyclicMetricB."""

    name: str = "cyclic_a"
    description: str = "Cyclic test metric A"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricB]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1


class CyclicMetricB(Metric):
    """Test metric that creates a cycle with CyclicMetricA."""

    name: str = "cyclic_b"
    description: str = "Cyclic test metric B"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [CyclicMetricA]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1


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

    name: str = "root_a"
    description: str = "Root A metric"
    unit: str = "count"
    base_value: int = 10

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = self.base_value


class RootB(Metric):
    """Root metric B - no dependencies."""

    name: str = "root_b"
    description: str = "Root B metric"
    unit: str = "count"
    base_value: int = 20

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = self.base_value


class RootC(Metric):
    """Root metric C - no dependencies (independent subgraph)."""

    name: str = "root_c"
    description: str = "Root C metric"
    unit: str = "count"
    base_value: int = 100

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = self.base_value


class SharedAB(Metric):
    """Metric with shared ancestors - depends on both RootA and RootB."""

    name: str = "shared_ab"
    description: str = "Shared AB metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootA, RootB]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Sum of both roots
        self.value = metrics[RootA].value + metrics[RootB].value


class BranchB(Metric):
    """Branch from RootB only."""

    name: str = "branch_b"
    description: str = "Branch B metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootB]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Triple the RootB value
        self.value = metrics[RootB].value * 3


class LeafC(Metric):
    """Leaf in independent subgraph - depends on RootC."""

    name: str = "leaf_c"
    description: str = "Leaf C metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [RootC]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Square root C
        self.value = metrics[RootC].value ** 2


class MidShared(Metric):
    """Middle layer - depends on SharedAB."""

    name: str = "mid_shared"
    description: str = "Mid shared metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [SharedAB]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[SharedAB].value + 5


class MidBranch(Metric):
    """Middle layer - depends on BranchB."""

    name: str = "mid_branch"
    description: str = "Mid branch metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [BranchB]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[BranchB].value * 2


class LeafAB(Metric):
    """Leaf with diamond pattern - depends on both MidShared and MidBranch."""

    name: str = "leaf_ab"
    description: str = "Leaf AB metric (diamond convergence)"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [MidShared, MidBranch]

    def calculate(self, context: Context, metrics: dict) -> None:
        # Product of both mid-level metrics
        self.value = metrics[MidShared].value * metrics[MidBranch].value


def dummy_provider(context: Context) -> Context:
    """Test provider that adds dummy data to context."""
    return {**context, "dummy_data": 100}


class ProviderDummyMetric(Metric):
    """Test metric that uses a provider."""

    name: str = "provider_dummy"
    description: str = "Uses dummy provider"
    unit: str = "count"

    @classmethod
    def providers(cls) -> list:
        return [dummy_provider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context["dummy_data"]


class FailingMetric(Metric):
    """Test metric that fails based on context."""

    name: str = "failing"
    description: str = "Fails when should_fail is True"
    unit: str = "count"

    def calculate(self, context: Context, metrics: dict) -> None:
        if context.get("should_fail"):
            raise ValueError("Intentional failure")
        self.value = 1


# Integration test metrics (must be at module level for ProcessPoolExecutor)


def integration_provider(context: Context) -> Context:
    """Provider that adds base_value to context."""
    return {**context, "base_value": 25}


class IntegrationBaseMetric(Metric):
    """Base metric for integration tests."""

    name: str = "base_metric"
    description: str = "Base test metric"
    unit: str = "units"
    threshold: int = 100

    @classmethod
    def providers(cls):
        return [integration_provider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context["base_value"]


class IntegrationDerivedMetric(Metric):
    """Derived metric for integration tests."""

    name: str = "derived_metric"
    description: str = "Derived test metric"
    unit: str = "units"
    multiplier: int = 2

    @classmethod
    def depends_on(cls):
        return [IntegrationBaseMetric]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = metrics[IntegrationBaseMetric].value * self.multiplier


def path_length_provider(context: Context) -> Context:
    """Provider that calculates path length."""
    path = context.get("path", "/unknown")
    return {**context, "path_length": len(path)}


class PathMetric(Metric):
    """Metric that uses path length from context."""

    name: str = "path_metric"
    description: str = "Calculates based on path"
    unit: str = "count"
    multiplier: int = 1

    @classmethod
    def providers(cls):
        return [path_length_provider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context["path_length"] * self.multiplier


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
