from typing import ClassVar

from checkup_dbt.metrics.base import DbtNodeCountMetric


class DbtModelsMetric(DbtNodeCountMetric):
    name: ClassVar[str] = "dbt_models"
    description: ClassVar[str] = "Total number of dbt models"
    unit: ClassVar[str] = "models"
    log_message: ClassVar[str] = "Found {value} models"
