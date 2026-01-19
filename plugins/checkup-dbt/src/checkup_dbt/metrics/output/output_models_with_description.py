from typing import ClassVar

from checkup_dbt.manifest_query import has_description, is_output_model
from checkup_dbt.metrics.base import DbtNodeCountMetric


def _is_output_model_with_description(node) -> bool:
    return is_output_model(node) and has_description(node)


class DbtOutputModelsWithDescriptionMetric(DbtNodeCountMetric):
    name: ClassVar[str] = "dbt_output_models_with_description"
    description: ClassVar[str] = "Number of output models with descriptions"
    unit: ClassVar[str] = "models"
    node_predicate = _is_output_model_with_description
    log_message: ClassVar[str] = "Found {value} output models with descriptions"
