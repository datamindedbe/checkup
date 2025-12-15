import logging

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.output.output_models import is_output_model

logger = logging.getLogger(__name__)


class DbtOutputColumnsWithoutDataTypeMetric(DbtMetric):
    name: str = "dbt_output_columns_without_data_type"
    description: str = "Number of columns in output models without data type"
    unit: str = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [
                (node.name, column_name)
                for node in manifest.nodes.values()
                if is_output_model(node)
                for column_name, column in node.columns.items()
                if column.data_type is None
            ]
        )
        logger.info(f"Found {self.value} output columns without data type")
