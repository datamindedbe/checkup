import logging
from typing import Any, Callable

from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context

from checkup_dbt.provider import DbtManifestProvider

NamingConventionChecker = Callable[[Context, Any], bool]

logger = logging.getLogger(__name__)


class DbtMetric(Metric):
    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DbtManifestProvider]
