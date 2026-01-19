"""Conveyor metrics for checkup."""

import logging
from typing import TYPE_CHECKING

from checkup import Context
from checkup.metric import Metric
from checkup_conveyor.api_client import ConveyorApiClient
from checkup_conveyor.provider import ConveyorProvider

if TYPE_CHECKING:
    from checkup.provider import Provider

logger = logging.getLogger(__name__)


class ConveyorMetric(Metric):
    """Base class for Conveyor-related metrics.

    Provides access to a ConveyorApiClient instance for making API calls.
    """

    def get_api_client(self, context: Context) -> ConveyorApiClient:
        """Get an API client configured from context.

        Args:
            context: Context dict containing ConveyorProvider data

        Returns:
            Configured ConveyorApiClient instance
        """
        provider_data = context[ConveyorProvider.name]
        return ConveyorApiClient(api_key=provider_data["api_key"])

    def get_project_name(self, context: Context) -> str:
        """Get project name from context.

        Args:
            context: Context dict containing ConveyorProvider data

        Returns:
            Project name string
        """
        return context[ConveyorProvider.name]["project_name"]

    def get_environment_name(self, context: Context) -> str:
        """Get environment name from context.

        Args:
            context: Context dict containing ConveyorProvider data

        Returns:
            Environment name string
        """
        return context[ConveyorProvider.name]["environment_name"]

    @classmethod
    def providers(cls) -> list[type["Provider"]]:
        return [ConveyorProvider]
