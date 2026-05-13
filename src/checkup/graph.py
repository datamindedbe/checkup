"""Dependency graph construction and topological sorting."""

import logging
from graphlib import CycleError, TopologicalSorter

from checkup.metric import Metric

logger = logging.getLogger(__name__)


def build_dependency_graph(
    metrics: list[type[Metric]],
) -> dict[type[Metric], list[type[Metric]]]:
    """Build dependency graph from metric classes.

    Args:
        metrics: List of metric classes

    Returns:
        Dict mapping each metric to its dependencies
    """
    graph: dict[type[Metric], list[type[Metric]]] = {}

    # Use a queue to process all metrics and their dependencies recursively
    to_process = list(metrics)

    while to_process:
        metric_cls = to_process.pop(0)
        if metric_cls in graph:
            continue

        deps = metric_cls.depends_on()
        graph[metric_cls] = deps
        logger.debug(
            "Added metric %s with %d dependencies",
            metric_cls.__name__,
            len(deps),
        )

        # Add dependencies to processing queue
        for dep in deps:
            if dep not in graph:
                to_process.append(dep)

    logger.debug("Built dependency graph with %d metrics", len(graph))
    return graph


def topological_sort(
    graph: dict[type[Metric], list[type[Metric]]],
) -> list[type[Metric]]:
    """Perform topological sort on dependency graph.

    Uses Python's graphlib.TopologicalSorter for reliable sorting.

    Args:
        graph: Dependency graph mapping metrics to their dependencies

    Returns:
        List of metrics in topological order (dependencies first)

    Raises:
        CycleError: If graph contains cycles
    """
    try:
        sorter = TopologicalSorter(graph)
        result = list(sorter.static_order())
        logger.debug("Topological sort produced %d metrics", len(result))
        return result
    except CycleError as e:
        logger.error("Circular dependency detected in metric graph: %s", e)
        raise
