"""ManifestQuery utility for querying dbt manifest data.

Provides a fluent interface for filtering and counting nodes in dbt manifests.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from dbt.artifacts.resources.types import NodeType
from dbt.contracts.graph.manifest import Manifest


class ManifestQuery:
    """Fluent query builder for dbt manifest nodes.

    Example:
        count = (
            ManifestQuery(manifest)
            .filter_by_type(NodeType.Model)
            .filter(lambda n: n.description != "")
            .count()
        )
    """

    def __init__(self, manifest: Manifest):
        """Initialize with a dbt manifest.

        Args:
            manifest: The dbt Manifest object to query
        """
        self._manifest = manifest
        self._nodes: Iterable[Any] | None = None
        self._filters: list[Callable[[Any], bool]] = []

    def _get_nodes(self) -> Iterable[Any]:
        """Get the current node set."""
        if self._nodes is not None:
            return self._nodes
        return self._manifest.nodes.values()

    def filter_by_type(self, resource_type: NodeType) -> "ManifestQuery":
        """Filter nodes by resource type.

        Args:
            resource_type: The NodeType to filter by (e.g., NodeType.Model)

        Returns:
            Self for chaining
        """
        self._filters.append(lambda n: n.resource_type == resource_type)
        return self

    def filter(self, predicate: Callable[[Any], bool]) -> "ManifestQuery":
        """Filter nodes by a custom predicate.

        Args:
            predicate: Function that returns True for nodes to include

        Returns:
            Self for chaining
        """
        self._filters.append(predicate)
        return self

    def _apply_filters(self) -> list[Any]:
        """Apply all filters and return matching nodes."""
        nodes = list(self._get_nodes())
        for f in self._filters:
            nodes = [n for n in nodes if f(n)]
        return nodes

    def count(self) -> int:
        """Count nodes matching all filters.

        Returns:
            Number of matching nodes
        """
        return len(self._apply_filters())

    def list(self) -> list[Any]:
        """Get list of nodes matching all filters.

        Returns:
            List of matching nodes
        """
        return self._apply_filters()

    def names(self) -> list[str]:
        """Get names of nodes matching all filters.

        Returns:
            List of node names, sorted alphabetically
        """
        return sorted(n.name for n in self._apply_filters())

    def count_columns(
        self, column_predicate: Callable[[Any, str, Any], bool] | None = None
    ) -> int:
        """Count columns across matching nodes.

        Args:
            column_predicate: Optional function(node, col_name, col) -> bool

        Returns:
            Total column count across matching nodes
        """
        nodes = self._apply_filters()
        count = 0
        for node in nodes:
            for col_name, col in node.columns.items():
                if column_predicate is None or column_predicate(node, col_name, col):
                    count += 1
        return count

    def columns(
        self, column_predicate: Callable[[Any, str, Any], bool] | None = None
    ) -> list[tuple[Any, str, Any]]:
        """Get columns across matching nodes.

        Args:
            column_predicate: Optional function(node, col_name, col) -> bool

        Returns:
            List of (node, column_name, column) tuples
        """
        nodes = self._apply_filters()
        result = []
        for node in nodes:
            for col_name, col in node.columns.items():
                if column_predicate is None or column_predicate(node, col_name, col):
                    result.append((node, col_name, col))
        return result

    def column_names(
        self, column_predicate: Callable[[Any, str, Any], bool] | None = None
    ) -> list[str]:
        """Get column names in 'model.column' format.

        Args:
            column_predicate: Optional function(node, col_name, col) -> bool

        Returns:
            List of 'model.column' strings, sorted
        """
        columns = self.columns(column_predicate)
        return sorted(f"{node.name}.{col_name}" for node, col_name, _ in columns)


# Common predicates for reuse
def has_description(node: Any) -> bool:
    """Check if node has a non-empty description."""
    return node.description != ""


def is_output_model(node: Any) -> bool:
    """Check if node is an output model (non-internal schema)."""
    return node.resource_type == NodeType.Model and not node.schema.endswith("__int")


def has_enforced_contract(node: Any) -> bool:
    """Check if node has an enforced contract."""
    return node.contract.enforced


def is_generic_test(node: Any) -> bool:
    """Check if node is a generic (data) test."""
    return getattr(node, "test_node_type", None) == "generic"


def is_singular_test(node: Any) -> bool:
    """Check if node is a singular (unit) test."""
    return getattr(node, "test_node_type", None) == "singular"


def is_column_test(node: Any) -> bool:
    """Check if test targets a specific column."""
    return hasattr(node, "column_name") and node.column_name is not None


def column_has_description(_node: Any, _col_name: str, col: Any) -> bool:
    """Check if column has a non-empty description."""
    return col.description != ""


def column_missing_data_type(_node: Any, _col_name: str, col: Any) -> bool:
    """Check if column is missing a data type."""
    return col.data_type is None


def output_column_missing_data_type(node: Any, _col_name: str, col: Any) -> bool:
    """Check if column in output model is missing a data type."""
    return is_output_model(node) and col.data_type is None
