from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup_dbt.metrics.base import DbtNodeCountMetric


class DbtTestsMetric(DbtNodeCountMetric):
    name: ClassVar[str] = "dbt_tests"
    description: ClassVar[str] = "Total number of dbt tests"
    unit: ClassVar[str] = "tests"
    resource_type: ClassVar[NodeType] = NodeType.Test
    log_message: ClassVar[str] = "Found {value} tests"
