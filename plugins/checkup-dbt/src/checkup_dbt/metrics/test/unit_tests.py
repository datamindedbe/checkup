from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup_dbt.manifest_query import is_singular_test
from checkup_dbt.metrics.base import DbtCountMetric


class DbtUnitTestsMetric(DbtCountMetric):
    name: str = "dbt_unit_tests"
    description: str = "Number of singular (unit) tests"
    unit: str = "tests"
    resource_type: ClassVar[NodeType] = NodeType.Test
    predicate = is_singular_test
    log_message: ClassVar[str] = "Found {value} unit tests"
