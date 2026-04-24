from typing import ClassVar

from checkup_dbt.metrics.base import CountTarget, DbtCountMetric


class DbtColumnsMetric(DbtCountMetric):
    name: str = "dbt_columns"
    description: str = "Total number of columns across all models"
    unit: str = "columns"
    count_target: ClassVar[CountTarget] = CountTarget.COLUMNS
    log_message: ClassVar[str] = "Found {value} columns"
