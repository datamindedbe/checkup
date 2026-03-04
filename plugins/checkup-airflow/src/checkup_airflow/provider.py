"""Airflow provider for checkup."""

import logging
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class AirflowProvider(Provider):
    """Provides Airflow context.

    Extracts metadata from an Airflow environment.

    Example:
        AirflowProvider()
    """

    name: ClassVar[str] = "airflow"

    def __init__(self):
        """Initialize AirflowProvider."""
        ...

    def provide(self) -> dict[str, Any]:
        """Get Airflow environment information.

        Returns:
            Dict with Airflow metadata.
        """
        logger.info("Getting Airflow environment info")

        return {}
