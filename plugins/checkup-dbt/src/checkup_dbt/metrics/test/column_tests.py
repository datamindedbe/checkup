from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup_dbt.manifest_query import is_column_test
from checkup_dbt.metrics.base import DbtCountMetric


class DbtColumnTestsMetric(DbtCountMetric):
    name: str = "dbt_column_tests"
    description: str = "Number of tests targeting specific columns"
    unit: str = "tests"
    resource_type: ClassVar[NodeType] = NodeType.Test
    predicate = is_column_test
    log_message: ClassVar[str] = "Found {value} column tests"
