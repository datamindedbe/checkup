from checkup import CheckHub



def test_integration():
    CheckHub().with_metrics([ConveyorLastDeploymentTime])