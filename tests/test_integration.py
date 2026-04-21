"""Integration tests for full checkup pipeline."""

from fixtures import (
    IntegrationBaseMetric,
    IntegrationDerivedMetric,
    IntegrationProvider,
    PathLengthProvider,
    PathMetric,
)

from checkup.hub import CheckHub
from checkup.providers.tags import TagProvider


def test_full_pipeline():
    """Test complete pipeline from provider through metric calculation."""
    result = (
        CheckHub()
        .with_metrics([IntegrationBaseMetric()])
        .with_providers([[IntegrationProvider()]])
        .measure()
    )

    assert len(result.measurements) == 1
    assert result.measurements[0].value == 25


def test_full_pipeline_with_both_metrics():
    """Test pipeline with dependent metrics."""
    result = (
        CheckHub()
        .with_metrics([IntegrationDerivedMetric()])
        .with_providers([[IntegrationProvider()]])
        .measure()
    )

    # Both base and derived metrics should be calculated
    assert len(result.measurements) == 2
    measurements_by_name = {m.metric.name: m for m in result.measurements}
    assert measurements_by_name["base_metric"].value == 25
    assert measurements_by_name["derived_metric"].value == 50  # 25 * 2


def test_multi_provider_set_pipeline():
    """Test pipeline across multiple provider sets."""
    result = (
        CheckHub()
        .with_metrics([PathMetric()])
        .with_providers(
            [
                [PathLengthProvider(path="/short"), TagProvider(name="short")],
                [
                    PathLengthProvider(path="/much/longer/path"),
                    TagProvider(name="long"),
                ],
            ]
        )
        .measure()
    )

    assert len(result.measurements) == 2

    measurements_by_name = {m.tags["name"]: m for m in result.measurements}
    assert measurements_by_name["short"].value == 6  # len("/short")
    assert measurements_by_name["long"].value == 17  # len("/much/longer/path")
