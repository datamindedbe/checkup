"""Python metrics for checkup."""
import os
from typing import Callable

import requests

from checkup import Context
from checkup.metric import Metric
from checkup_conveyor.provider import ConveyorProvider


class ConveyorMetric(Metric):
    """Base class for Conveyor-related metrics."""

    base_url: str = "https://app.conveyordata.com/api/v2"

    def get_conveyor_api_headers(self, context: Context):
        api_key = context['ConveyorProvider']['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        return headers

    def get_conveyor_project_id(self, context):
        r = requests.get(f"{self.base_url}/projects",
                     headers=self.get_conveyor_api_headers(context),
                     params={"name": context['ConveyorProvider']['project_name']},
                     ).json()
        return r['projects'][0]['id']

    def get_environment_id(self, context):
        r = requests.get(f"{self.base_url}/environments",
                     headers=self.get_conveyor_api_headers(context),
                     params={"name": context['ConveyorProvider']['environment_name']},
        ).json()
        return r['environments'][0]['id']

    @classmethod
    def providers(cls) -> list[type["Provider"]]:
        return [ConveyorProvider]

