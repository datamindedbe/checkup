from typing import ClassVar

from checkup_dbt.metrics.base import DbtCountMetric


class DbtModelsMetric(DbtCountMetric):
    name: str = "dbt_models"
    description: str = "Total number of dbt models"
    unit: str = "models"
    log_message: ClassVar[str] = "Found {value} models"
