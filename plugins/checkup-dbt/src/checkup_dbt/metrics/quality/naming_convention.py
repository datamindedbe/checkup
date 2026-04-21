import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric, NamingConventionChecker

logger = logging.getLogger(__name__)


class DbtModelsNotAdheringToNamingConventionMetric(DbtMetric):
    """
    Metric for checking model naming conventions.

    This metric requires a custom checker function that defines the naming
    convention. Use with_checker() to create a configured metric class.
    """

    name: ClassVar[str] = "dbt_models_not_adhering_to_naming_convention"
    description: ClassVar[str] = "Number of models not adhering to naming convention"
    unit: ClassVar[str] = "models"

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

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        manifest = self.get_manifest(context)
        checker = self.get_checker()

        non_adhering_models = [
            node.name
            for node in manifest.nodes.values()
            if node.resource_type == NodeType.Model and not checker(context, node)
        ]

        value = len(non_adhering_models)
        diagnostic = ""
        if non_adhering_models:
            diagnostic = f"Models not adhering to naming convention: {', '.join(sorted(non_adhering_models))}"
        logger.info(f"Found {value} models not adhering to naming convention")
        return self.measure(value=value, diagnostic=diagnostic)
