import logging
from typing import ClassVar

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.output.output_models import is_output_model
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtOutputColumnsWithoutDataTypeMetric(DbtMetric):
    name: ClassVar[str] = "dbt_output_columns_without_data_type"
    description: ClassVar[str] = "Number of columns in output models without data type"
    unit: ClassVar[str] = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        columns_without_data_type = [
            f"{node.name}.{column_name}"
            for node in manifest.nodes.values()
            if is_output_model(node)
            for column_name, column in node.columns.items()
            if column.data_type is None
        ]
        self.value = len(columns_without_data_type)
        if columns_without_data_type:
            self.diagnostic = (
                f"Output columns without data type: {', '.join(sorted(columns_without_data_type))}"
            )
        logger.info(f"Found {self.value} output columns without data type")
