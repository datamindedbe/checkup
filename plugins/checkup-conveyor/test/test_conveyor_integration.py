import os

import pytest
from checkup_conveyor import ConveyorProvider
from checkup_conveyor.conveyor_metric import (
    ConveyorIsDirtyDeployment,
    ConveyorLastDeploymentTime,
    ConveyorLastRunStatus,
)

from checkup import CheckHub


@pytest.mark.skipif(
    not os.environ.get("CONVEYOR_API_KEY"),
    reason="CONVEYOR_API_KEY environment variable not set",
)
def test_conveyor_integration():
    api_key = os.environ.get("CONVEYOR_API_KEY", "")
    environment_name = os.environ.get("CONVEYOR_ENVIRONMENT", "production")
    project_name = os.environ.get("CONVEYOR_PROJECT", "activity-centers")

    r = (
        CheckHub()
        .with_metrics(
            [
                ConveyorLastDeploymentTime,
                ConveyorIsDirtyDeployment,
                ConveyorLastRunStatus,
            ]
        )
        .with_providers(
            [
                [
                    ConveyorProvider(
                        project_name=project_name,
                        api_key=api_key,
                        environment_name=environment_name,
                    )
                ]
            ]
        )
        .measure()
    )
    assert r is not None
