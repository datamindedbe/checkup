from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup_dbt.metrics.base import DbtCountMetric


class DbtTestsMetric(DbtCountMetric):
    name: str = "dbt_tests"
    description: str = "Total number of dbt tests"
    unit: str = "tests"
    resource_type: ClassVar[NodeType] = NodeType.Test
    log_message: ClassVar[str] = "Found {value} tests"
