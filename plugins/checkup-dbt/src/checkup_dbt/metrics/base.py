from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, ClassVar

from dbt.artifacts.resources.types import NodeType
from dbt.contracts.graph.manifest import Manifest

from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context
from checkup_dbt.manifest_query import ManifestQuery
from checkup_dbt.provider import DbtManifestProvider

NamingConventionChecker = Callable[[Context, Any], bool]

logger = logging.getLogger(__name__)


class DbtMetric(Metric):
    """Base class for dbt metrics."""

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DbtManifestProvider]

    def get_manifest(self, context: Context) -> Manifest:
        """Get the manifest from context.

        Args:
            context: The context dict

        Returns:
            The dbt Manifest object
        """
        return context[DbtManifestProvider.name]["manifest"]

    def query(self, context: Context) -> ManifestQuery:
        """Create a ManifestQuery for the context's manifest.

        Args:
            context: The context dict

        Returns:
            ManifestQuery instance for fluent querying
        """
        return ManifestQuery(self.get_manifest(context))


class DbtNodeCountMetric(DbtMetric):
    """Base class for metrics that count nodes matching criteria.

    Subclasses should define:
    - name, description, unit (ClassVars)
    - resource_type: The NodeType to filter by
    - node_predicate (optional): Additional filter function
    - log_message: Template for log message (uses {value})
    """

    resource_type: ClassVar[NodeType] = NodeType.Model
    node_predicate: ClassVar[Callable[[Any], bool] | None] = None
    log_message: ClassVar[str] = "Found {value} nodes"

    def calculate(self, context: Context, metrics: dict) -> None:
        cls = type(self)
        query = self.query(context).filter_by_type(cls.resource_type)
        if cls.node_predicate:
            query = query.filter(cls.node_predicate)
        self.value = query.count()
        logger.info(cls.log_message.format(value=self.value))


class DbtColumnCountMetric(DbtMetric):
    """Base class for metrics that count columns matching criteria.

    Subclasses should define:
    - name, description, unit (ClassVars)
    - resource_type: The NodeType to filter by (default: Model)
    - node_predicate (optional): Filter for nodes
    - column_predicate (optional): Filter for columns
    - log_message: Template for log message (uses {value})
    """

    resource_type: ClassVar[NodeType] = NodeType.Model
    node_predicate: ClassVar[Callable[[Any], bool] | None] = None
    column_predicate: ClassVar[Callable[[Any, str, Any], bool] | None] = None
    log_message: ClassVar[str] = "Found {value} columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        cls = type(self)
        query = self.query(context).filter_by_type(cls.resource_type)
        if cls.node_predicate:
            query = query.filter(cls.node_predicate)
        self.value = query.count_columns(cls.column_predicate)
        logger.info(cls.log_message.format(value=self.value))


class DbtDiagnosticMetric(DbtMetric):
    """Base class for metrics that count and list items with diagnostics.

    Produces both a count and a diagnostic listing the items.
    Can count either nodes or columns based on the count_columns flag.

    Subclasses should define:
    - name, description, unit (ClassVars)
    - resource_type: The NodeType to filter by
    - node_predicate (optional): Filter for nodes
    - column_predicate (optional): Filter for columns (when count_columns=True)
    - diagnostic_prefix: Prefix for diagnostic message
    - log_message: Template for log message (uses {value})
    - count_columns: Set to True to count columns instead of nodes
    """

    resource_type: ClassVar[NodeType] = NodeType.Model
    node_predicate: ClassVar[Callable[[Any], bool] | None] = None
    column_predicate: ClassVar[Callable[[Any, str, Any], bool] | None] = None
    diagnostic_prefix: ClassVar[str] = "Items"
    log_message: ClassVar[str] = "Found {value} items"
    count_columns: ClassVar[bool] = False

    def calculate(self, context: Context, metrics: dict) -> None:
        cls = type(self)
        query = self.query(context).filter_by_type(cls.resource_type)
        if cls.node_predicate:
            query = query.filter(cls.node_predicate)

        if cls.count_columns:
            names = query.column_names(cls.column_predicate)
        else:
            names = query.names()

        self.value = len(names)
        if names:
            self.diagnostic = f"{cls.diagnostic_prefix}: {', '.join(names)}"
        logger.info(cls.log_message.format(value=self.value))


# Alias for backward compatibility
DbtColumnDiagnosticMetric = DbtDiagnosticMetric
