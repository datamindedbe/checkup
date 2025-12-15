import logging

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric, NamingConventionChecker

logger = logging.getLogger(__name__)


class DbtModelsNotAdheringToNamingConventionMetric(DbtMetric):
    name: str = "dbt_models_not_adhering_to_naming_convention"
    description: str = "Number of models not adhering to naming convention"
    unit: str = "models"

    @classmethod
    def get_checker(cls) -> NamingConventionChecker:
        raise NotImplementedError(
            "Subclasses must override get_checker() or use with_checker() to create a metric"
        )

    @classmethod
    def with_checker(
        cls, checker: NamingConventionChecker
    ) -> type["DbtModelsNotAdheringToNamingConventionMetric"]:
        class CustomNamingConventionMetric(cls):
            @classmethod
            def get_checker(cls) -> NamingConventionChecker:
                return checker

        return CustomNamingConventionMetric

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        checker = self.get_checker()

        non_adhering_models = [
            node
            for node in manifest.nodes.values()
            if node.resource_type == NodeType.Model and not checker(context, node)
        ]

        self.value = len(non_adhering_models)
        logger.info(f"Found {self.value} models not adhering to naming convention")
