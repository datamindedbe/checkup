"""Tests for dependency graph construction and topological sorting."""

from graphlib import CycleError

import pytest
from fixtures import (
    BranchB,
    CyclicMetricA,
    CyclicMetricB,
    DependentDummyMetric,
    DummyMetric,
    LeafAB,
    LeafC,
    Level2Metric,
    Level3Metric,
    MidBranch,
    MidShared,
    RootA,
    RootB,
    RootC,
    SharedAB,
)

from checkup.graph import build_dependency_graph, topological_sort
from checkup.measurement import Measurements
from checkup.metric import Metric


class TestBuildDependencyGraph:
    def test_no_dependencies(self):
        """Test building graph for metric with no dependencies."""
        graph = build_dependency_graph([DummyMetric])

        assert graph == {DummyMetric: []}

    def test_with_dependencies(self):
        """Test building graph for metrics with dependencies."""
        graph = build_dependency_graph([DependentDummyMetric, DummyMetric])

        assert graph == {DummyMetric: [], DependentDummyMetric: [DummyMetric]}

    def test_auto_adds_missing_dependencies(self):
        """Test that missing dependencies are automatically added."""
        graph = build_dependency_graph([DependentDummyMetric])

        assert DummyMetric in graph
        assert DependentDummyMetric in graph


class TestTopologicalSort:
    def test_no_dependencies(self):
        """Test topological sort with no dependencies."""
        graph: dict[type[Metric], list[type[Metric]]] = {DummyMetric: []}

        result = topological_sort(graph)

        assert result == [DummyMetric]

    def test_with_dependencies(self):
        """Test topological sort with dependencies."""
        graph = {DummyMetric: [], DependentDummyMetric: [DummyMetric]}

        result = topological_sort(graph)

        assert result.index(DummyMetric) < result.index(DependentDummyMetric)
        assert len(result) == 2

    def test_deep_chain(self):
        """Test topological sort with depth 3 dependency chain.

        Chain: DummyMetric -> DependentDummyMetric -> Level2Metric -> Level3Metric
        """
        graph = build_dependency_graph([Level3Metric])

        result = topological_sort(graph)

        assert len(result) == 4
        assert result.index(DummyMetric) < result.index(DependentDummyMetric)
        assert result.index(DependentDummyMetric) < result.index(Level2Metric)
        assert result.index(Level2Metric) < result.index(Level3Metric)

    def test_deep_chain_calculation(self, empty_context):
        """Test that deep dependency chain calculates correctly.

        DummyMetric(10) -> DependentDummyMetric(20) -> Level2Metric(30) -> Level3Metric(900)
        """
        graph = build_dependency_graph([Level3Metric])
        order = topological_sort(graph)

        calculated = Measurements()

        for metric_cls in order:
            if metric_cls is DummyMetric:
                metric: Metric = DummyMetric(expected_value=10)
            else:
                metric = metric_cls()  # type: ignore
            measurement = metric.calculate(empty_context, calculated)
            calculated.append(metric_cls, measurement)

        assert calculated.get(DummyMetric).value == 10
        assert calculated.get(DependentDummyMetric).value == 20  # 10 * 2
        assert calculated.get(Level2Metric).value == 30  # 20 + 10
        assert calculated.get(Level3Metric).value == 900  # 30 ** 2


class TestCycleDetection:
    def test_direct_cycle(self):
        """Test that topological sort detects direct cycles between two metrics."""
        graph = {
            CyclicMetricA: [CyclicMetricB],
            CyclicMetricB: [CyclicMetricA],
        }

        with pytest.raises(CycleError):
            topological_sort(graph)

    def test_via_build_graph(self):
        """Test cycle detection when building graph from cyclic metrics."""
        graph = build_dependency_graph([CyclicMetricA])

        with pytest.raises(CycleError):
            topological_sort(graph)


class TestComplexDependencyGraph:
    def test_structure(self):
        """Test building graph with shared ancestors and multiple branches.

        Graph structure:
            RootA     RootB                   RootC
              \\       /   \\                     |
               \\     /     \\                    |
              SharedAB    BranchB             LeafC
                  |          |
              MidShared   MidBranch
                   \\       /
                    LeafAB
        """
        graph = build_dependency_graph([LeafAB, LeafC])

        # All metrics should be included
        assert RootA in graph
        assert RootB in graph
        assert RootC in graph
        assert SharedAB in graph
        assert BranchB in graph
        assert LeafC in graph
        assert MidShared in graph
        assert MidBranch in graph
        assert LeafAB in graph

        # Verify dependencies
        assert graph[RootA] == []
        assert graph[RootB] == []
        assert graph[RootC] == []
        assert set(graph[SharedAB]) == {RootA, RootB}
        assert graph[BranchB] == [RootB]
        assert graph[LeafC] == [RootC]
        assert graph[MidShared] == [SharedAB]
        assert graph[MidBranch] == [BranchB]
        assert set(graph[LeafAB]) == {MidShared, MidBranch}

    def test_topological_order(self):
        """Test topological sort respects all dependency constraints."""
        graph = build_dependency_graph([LeafAB, LeafC])
        order = topological_sort(graph)

        # Roots must come before their dependents
        assert order.index(RootA) < order.index(SharedAB)
        assert order.index(RootB) < order.index(SharedAB)
        assert order.index(RootB) < order.index(BranchB)
        assert order.index(RootC) < order.index(LeafC)

        # Mid-level must come before leaves
        assert order.index(SharedAB) < order.index(MidShared)
        assert order.index(BranchB) < order.index(MidBranch)
        assert order.index(MidShared) < order.index(LeafAB)
        assert order.index(MidBranch) < order.index(LeafAB)

    def test_calculation(self, empty_context):
        """Test full calculation of complex dependency graph.

        Expected values:
        - RootA: 10
        - RootB: 20
        - RootC: 100
        - SharedAB: 10 + 20 = 30
        - BranchB: 20 * 3 = 60
        - LeafC: 100 ** 2 = 10000
        - MidShared: 30 + 5 = 35
        - MidBranch: 60 * 2 = 120
        - LeafAB: 35 * 120 = 4200
        """
        graph = build_dependency_graph([LeafAB, LeafC])
        order = topological_sort(graph)

        calculated = Measurements()

        for metric_cls in order:
            metric = metric_cls()  # type: ignore
            measurement = metric.calculate(empty_context, calculated)
            calculated.append(metric_cls, measurement)

        # Verify all calculations
        assert calculated.get(RootA).value == 10
        assert calculated.get(RootB).value == 20
        assert calculated.get(RootC).value == 100
        assert calculated.get(SharedAB).value == 30  # 10 + 20
        assert calculated.get(BranchB).value == 60  # 20 * 3
        assert calculated.get(LeafC).value == 10000  # 100 ** 2
        assert calculated.get(MidShared).value == 35  # 30 + 5
        assert calculated.get(MidBranch).value == 120  # 60 * 2
        assert calculated.get(LeafAB).value == 4200  # 35 * 120

    def test_via_checkhub(self):
        """Test complex graph calculation through CheckHub."""
        from checkup import CheckHub

        result = CheckHub().with_metrics([LeafAB(), LeafC()]).measure()

        measurements_by_name = {m.metric.name: m for m in result.measurements}

        # All 9 metrics returned (direct and indirect)
        assert len(result.measurements) == 9

        # Only requested metrics are marked as direct
        assert result.direct_metric_names == {"leaf_ab", "leaf_c"}

        # Verify calculated values
        assert measurements_by_name["leaf_ab"].value == 4200
        assert measurements_by_name["leaf_c"].value == 10000

    def test_shared_ancestor_calculated_once(self, empty_context):
        """Test that RootB (shared by SharedAB and BranchB) is only calculated once.

        This verifies the framework doesn't re-calculate metrics that appear
        multiple times in the dependency graph.
        """
        graph = build_dependency_graph([LeafAB])
        order = topological_sort(graph)

        # Track how many times each metric class is calculated
        calculation_counts: dict[type[Metric], int] = {}
        calculated = Measurements()

        for metric_cls in order:
            calculation_counts[metric_cls] = calculation_counts.get(metric_cls, 0) + 1
            metric = metric_cls()  # type: ignore
            measurement = metric.calculate(empty_context, calculated)
            calculated.append(metric_cls, measurement)

        # Each metric should appear exactly once in the execution order
        for metric_cls, count in calculation_counts.items():
            assert count == 1, f"{metric_cls.__name__} was calculated {count} times"

        # Specifically verify RootB (shared ancestor) is only calculated once
        assert calculation_counts[RootB] == 1

    def test_independent_subgraphs(self):
        """Test that independent subgraphs can coexist without interference."""
        from checkup import CheckHub

        # Only request LeafC (independent subgraph) - returns LeafC and RootC
        result = CheckHub().with_metrics([LeafC()]).measure()

        assert len(result.measurements) == 2
        assert result.direct_metric_names == {"leaf_c"}
        measurements_by_name = {m.metric.name: m for m in result.measurements}
        assert measurements_by_name["leaf_c"].value == 10000

        # Request both subgraphs - returns all 9 metrics
        result = CheckHub().with_metrics([LeafAB(), LeafC()]).measure()

        assert len(result.measurements) == 9
        assert result.direct_metric_names == {"leaf_ab", "leaf_c"}
