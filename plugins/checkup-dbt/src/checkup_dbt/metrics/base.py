import logging
from typing import Any, Callable

from checkup.metric import Metric
from checkup.types import Context

from checkup_dbt.provider import dbt_manifest_provider

NamingConventionChecker = Callable[[Context, Any], bool]

logger = logging.getLogger(__name__)


class DbtMetric(Metric):
    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        return [dbt_manifest_provider]
