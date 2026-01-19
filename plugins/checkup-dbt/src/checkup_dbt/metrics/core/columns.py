from typing import ClassVar

from checkup_dbt.metrics.base import DbtColumnCountMetric


class DbtColumnsMetric(DbtColumnCountMetric):
    name: ClassVar[str] = "dbt_columns"
    description: ClassVar[str] = "Total number of columns across all models"
    unit: ClassVar[str] = "columns"
    log_message: ClassVar[str] = "Found {value} columns"
