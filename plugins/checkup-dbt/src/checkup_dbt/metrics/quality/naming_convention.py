import logging

from dbt.artifacts.resources.types import NodeType

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric, NamingConventionChecker

logger = logging.getLogger(__name__)


class DbtModelsNotAdheringToNamingConventionMetric(DbtMetric):
    """
    Metric for checking model naming conventions.

    Requires a checker function that defines the naming convention.

    Example:
        DbtModelsNotAdheringToNamingConventionMetric(
            name="dbt_staging_naming",
            checker=lambda ctx, node: node.name.startswith("stg_")
        )
    """

    name: str = "dbt_models_not_adhering_to_naming_convention"
    description: str = "Number of models not adhering to naming convention"
    unit: str = "models"

    checker: NamingConventionChecker

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        manifest = self.get_manifest(context)

        non_adhering_models = [
            node.name
            for node in manifest.nodes.values()
            if node.resource_type == NodeType.Model and not self.checker(context, node)
        ]

        value = len(non_adhering_models)
        diagnostic = ""
        if non_adhering_models:
            diagnostic = f"Models not adhering to naming convention: {', '.join(sorted(non_adhering_models))}"
        logger.info(f"Found {value} models not adhering to naming convention")
        return self.measure(value=value, diagnostic=diagnostic)
