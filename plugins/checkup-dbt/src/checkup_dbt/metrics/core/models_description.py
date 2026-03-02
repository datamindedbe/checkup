from typing import ClassVar

from checkup_dbt.manifest_query import has_description, without_description
from checkup_dbt.metrics.base import DbtCountMetric


class DbtModelsWithDescriptionMetric(DbtCountMetric):
    name: ClassVar[str] = "dbt_models_with_description"
    description: ClassVar[str] = "Number of models with descriptions"
    unit: ClassVar[str] = "models"
    predicate = has_description
    log_message: ClassVar[str] = "Found {value} models with descriptions"


class DbtModelsWithoutDescriptionMetric(DbtCountMetric):
    name: ClassVar[str] = "dbt_models_without_description"
    description: ClassVar[str] = "Number of models without descriptions"
    unit: ClassVar[str] = "models"
    predicate = without_description
    log_message: ClassVar[str] = "Found {value} models without descriptions"
