from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum, auto
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


class CountTarget(Enum):
    """What to count in a diagnostic metric."""

    NODES = auto()
    COLUMNS = auto()


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


class DbtCountMetric(DbtMetric):
    """Base class for metrics that count nodes or columns.

    Subclasses should define:
    - name, description, unit (ClassVars)
    - resource_type: The NodeType to filter by
    - count_target: What to count (NODES or COLUMNS)
    - predicate (optional): Filter function
      - For NODES: Callable[[node], bool]
      - For COLUMNS: Callable[[node, col_name, col], bool]
    - log_message: Template for log message (uses {value})
    """

    resource_type: ClassVar[NodeType] = NodeType.Model
    count_target: ClassVar[CountTarget] = CountTarget.NODES
    predicate: ClassVar[Callable[..., bool] | None] = None
    log_message: ClassVar[str] = "Found {value} items"

    def calculate(self, context: Context, metrics: dict) -> None:
        cls = type(self)
        query = self.query(context).filter_by_type(cls.resource_type)

        if cls.count_target == CountTarget.COLUMNS:
            self.value = query.count_columns(cls.predicate)
        else:
            if cls.predicate:
                query = query.filter(cls.predicate)
            self.value = query.count()

        logger.info(cls.log_message.format(value=self.value))


class DbtDiagnosticMetric(DbtMetric):
    """Base class for metrics that count and list items with diagnostics.

    Produces both a count and a diagnostic listing the items.

    Subclasses should define:
    - name, description, unit (ClassVars)
    - resource_type: The NodeType to filter by
    - count_target: What to count (NODES or COLUMNS)
    - predicate (optional): Filter function
      - For NODES: Callable[[node], bool]
      - For COLUMNS: Callable[[node, col_name, col], bool]
    - diagnostic_prefix: Prefix for diagnostic message
    - log_message: Template for log message (uses {value})
    """

    resource_type: ClassVar[NodeType] = NodeType.Model
    count_target: ClassVar[CountTarget] = CountTarget.NODES
    predicate: ClassVar[Callable[..., bool] | None] = None
    diagnostic_prefix: ClassVar[str] = "Items"
    log_message: ClassVar[str] = "Found {value} items"

    def calculate(self, context: Context, metrics: dict) -> None:
        cls = type(self)
        query = self.query(context).filter_by_type(cls.resource_type)

        if cls.count_target == CountTarget.COLUMNS:
            names = query.column_names(cls.predicate)
        else:
            if cls.predicate:
                query = query.filter(cls.predicate)
            names = query.names()

        self.value = len(names)
        if names:
            self.diagnostic = f"{cls.diagnostic_prefix}: {', '.join(names)}"
        logger.info(cls.log_message.format(value=self.value))
