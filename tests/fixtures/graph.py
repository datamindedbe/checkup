from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.types import Context


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
