"""Python metrics for checkup."""
import logging
import os
from typing import Callable

import requests

from checkup import Context
from checkup.metric import Metric
from checkup_conveyor.provider import ConveyorProvider

logger = logging.getLogger(__name__)


class ConveyorMetric(Metric):
    """Base class for Conveyor-related metrics."""

    base_url: str = "https://app.conveyordata.com/api/v2"

    def get_conveyor_api_headers(self, context: Context):
        api_key = context['ConveyorProvider']['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        return headers

    def get_conveyor_project_id(self, context) -> str | None:
        project_name = context['ConveyorProvider']['project_name']
        r = requests.get(f"{self.base_url}/projects",
                     headers=self.get_conveyor_api_headers(context),
                     params={"name": project_name},
                     ).json()
        projects = r.get('projects', [])
        if not projects:
            logger.warning("No Conveyor project found with name: %s", project_name)
            return None
        return projects[0]['id']

    def get_environment_id(self, context) -> str | None:
        env_name = context['ConveyorProvider']['environment_name']
        r = requests.get(f"{self.base_url}/environments",
                     headers=self.get_conveyor_api_headers(context),
                     params={"name": env_name},
        ).json()
        environments = r.get('environments', [])
        if not environments:
            logger.warning("No Conveyor environment found with name: %s", env_name)
            return None
        return environments[0]['id']

    @classmethod
    def providers(cls) -> list[type["Provider"]]:
        return [ConveyorProvider]

