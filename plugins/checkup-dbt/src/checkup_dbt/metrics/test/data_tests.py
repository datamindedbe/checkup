from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup_dbt.manifest_query import is_generic_test
from checkup_dbt.metrics.base import DbtNodeCountMetric


class DbtDataTestsMetric(DbtNodeCountMetric):
    name: ClassVar[str] = "dbt_data_tests"
    description: ClassVar[str] = "Number of generic (data) tests"
    unit: ClassVar[str] = "tests"
    resource_type: ClassVar[NodeType] = NodeType.Test
    node_predicate = is_generic_test
    log_message: ClassVar[str] = "Found {value} data tests"
