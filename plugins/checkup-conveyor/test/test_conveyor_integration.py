from checkup_conveyor import ConveyorProvider
from checkup_conveyor.conveyor_metric import (
    ConveyorIsDirtyDeployment,
    ConveyorLastDeploymentTime,
    ConveyorLastRunStatus,
)

from checkup import CheckHub


def test_conveyor_integration():
    r = (
        CheckHub()
        .with_metrics(
            [
                ConveyorLastDeploymentTime,
                ConveyorIsDirtyDeployment,
                ConveyorLastRunStatus,
            ]
        )
        .with_providers([[ConveyorProvider(project_name="activity-centers")]])
        .measure()
    )
    assert r is not None
