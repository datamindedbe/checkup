from checkup import CheckHub
from checkup_conveyor.conveyor_metric import ConveyorLastDeploymentTime


def test_conveyor_integration():
    r = CheckHub().with_metrics([ConveyorLastDeploymentTime]).measure()
    assert r is not None