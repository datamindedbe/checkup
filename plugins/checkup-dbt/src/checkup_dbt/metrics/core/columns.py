from typing import ClassVar

from checkup_dbt.metrics.base import CountTarget, DbtCountMetric


class DbtColumnsMetric(DbtCountMetric):
    name: ClassVar[str] = "dbt_columns"
    description: ClassVar[str] = "Total number of columns across all models"
    unit: ClassVar[str] = "columns"
    count_target: ClassVar[CountTarget] = CountTarget.COLUMNS
    log_message: ClassVar[str] = "Found {value} columns"
