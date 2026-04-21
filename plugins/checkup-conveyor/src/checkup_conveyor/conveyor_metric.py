import logging
from typing import ClassVar

import requests

from checkup import Context
from checkup.metric import Measurement, Metric
from checkup_conveyor import ConveyorMetric

logger = logging.getLogger(__name__)


class ConveyorLastDeploymentTime(ConveyorMetric):
    name: ClassVar[str] = "Conveyor Last Deployment Time"
    description: ClassVar[str] = "Time of the last deployment in Conveyor"
    unit: ClassVar[str] = "timestamp"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        proj_id = self.get_conveyor_project_id(context)
        if proj_id is None:
            return self.measure(value=None)
        r = requests.get(
            f"{self.base_url}/projects/{proj_id}/deployments",
            headers=self.get_conveyor_api_headers(context),
        ).json()
        deployments = r.get("deployment", [])
        if not deployments:
            logger.warning("No deployments found for project %s", proj_id)
            return self.measure(value=None)
        return self.measure(
            value=deployments[0]["deployedOn"],
            diagnostic="Deploy the project again to update this value.",
        )


class ConveyorIsDirtyDeployment(ConveyorMetric):
    name: ClassVar[str] = "Conveyor Is Dirty Deployment"
    description: ClassVar[str] = "True if the last deployment was dirty"
    unit: ClassVar[str] = "boolean"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        proj_id = self.get_conveyor_project_id(context)
        if proj_id is None:
            return self.measure(value=None)
        r = requests.get(
            f"{self.base_url}/projects/{proj_id}/builds",
            headers=self.get_conveyor_api_headers(context),
        ).json()
        builds = r.get("builds", [])
        if not builds:
            logger.warning("No builds found for project %s", proj_id)
            return self.measure(value=None)
        is_dirty = builds[0]["gitHash"].endswith(".dirty")
        diagnostic = (
            "Commit changes to git, and deploy the project again." if is_dirty else ""
        )
        return self.measure(value=is_dirty, diagnostic=diagnostic)


class ConveyorLastRunStatus(ConveyorMetric):
    name: ClassVar[str] = "Conveyor Last Run Status"
    description: ClassVar[str] = "Status of the last run in Conveyor"
    unit: ClassVar[str] = "string"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        proj_id = self.get_conveyor_project_id(context)
        if proj_id is None:
            return self.measure(value=None)
        env_id = self.get_environment_id(context)
        if env_id is None:
            return self.measure(value=None)
        r = requests.get(
            f"{self.base_url}/environments/{env_id}/application_runs",
            params={
                "sortedOn": "SortedOn_None",
                "sortedOrder": "SortedOrder_None",
                "projectId": proj_id,
            },
            headers=self.get_conveyor_api_headers(context),
        ).json()
        runs = r.get("applicationRuns", [])
        if not runs:
            logger.warning(
                "No application runs found for project %s in environment %s",
                proj_id,
                env_id,
            )
            return self.measure(value=None)
        return self.measure(value=runs[0]["phase"])
