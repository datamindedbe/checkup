"""Dependency graph construction and topological sorting."""

from graphlib import TopologicalSorter
from typing import Type

from checkup.metric import Metric


def build_dependency_graph(
    metrics: list[Type[Metric]],
) -> dict[Type[Metric], list[Type[Metric]]]:
    """Build dependency graph from metric classes.

    Args:
        metrics: List of metric classes

    Returns:
        Dict mapping each metric to its dependencies
    """
    graph: dict[Type[Metric], list[Type[Metric]]] = {}

    # Use a queue to process all metrics and their dependencies recursively
    to_process = list(metrics)

    while to_process:
        metric_cls = to_process.pop(0)
        if metric_cls in graph:
            continue

        deps = metric_cls.depends_on()
        graph[metric_cls] = deps

        # Add dependencies to processing queue
        for dep in deps:
            if dep not in graph:
                to_process.append(dep)

    return graph


def topological_sort(
    graph: dict[Type[Metric], list[Type[Metric]]],
) -> list[Type[Metric]]:
    """Perform topological sort on dependency graph.

    Uses Python's graphlib.TopologicalSorter for reliable sorting.

    Args:
        graph: Dependency graph mapping metrics to their dependencies

    Returns:
        List of metrics in topological order (dependencies first)

    Raises:
        ValueError: If graph contains cycles
    """
    sorter = TopologicalSorter(graph)
    return list(sorter.static_order())
