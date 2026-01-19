from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup_dbt.manifest_query import is_singular_test
from checkup_dbt.metrics.base import DbtNodeCountMetric


class DbtUnitTestsMetric(DbtNodeCountMetric):
    name: ClassVar[str] = "dbt_unit_tests"
    description: ClassVar[str] = "Number of singular (unit) tests"
    unit: ClassVar[str] = "tests"
    resource_type: ClassVar[NodeType] = NodeType.Test
    node_predicate = is_singular_test
    log_message: ClassVar[str] = "Found {value} unit tests"
