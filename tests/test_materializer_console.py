from fixtures import DummyMetric, capture_output

from checkup.materializers import ConsoleMaterializer


def test_console_materializer():
    """Test console output materializer with two-level grouping."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42)

    output = capture_output(
        ConsoleMaterializer(group_tags=["domain", "project"]), [measurement], {"dummy"}
    )

    assert "dummy" in output
    assert "42" in output


def test_console_materializer_no_grouping():
    """Test console materializer without grouping."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42)

    output = capture_output(ConsoleMaterializer(), [measurement], {"dummy"})

    assert "dummy" in output
    assert "42" in output


def test_console_materializer_single_grouping():
    """Test console materializer with single-level grouping."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42, tags={"domain": "Analytics"})

    output = capture_output(
        ConsoleMaterializer(group_tags=["domain"]), [measurement], {"dummy"}
    )

    assert "dummy" in output
    assert "42" in output
    assert "domain: Analytics" in output


def test_console_materializer_three_level_grouping():
    """Test console materializer with three-level grouping."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(
        value=42, tags={"domain": "Analytics", "project": "Core", "env": "prod"}
    )

    output = capture_output(
        ConsoleMaterializer(group_tags=["domain", "project", "env"]),
        [measurement],
        {"dummy"},
    )

    assert "dummy" in output
    assert "42" in output
    assert "domain: Analytics" in output
    assert "project: Core" in output
    assert "env: prod" in output


def test_console_pretty_boolean_glyphs():
    """
    Console pretty mode renders booleans as check or cross glyphs.
    """

    measurements = [
        DummyMetric(name="linked", unit="boolean").measure(value=True),
        DummyMetric(name="clean", unit="boolean").measure(value=False),
    ]

    output = capture_output(
        ConsoleMaterializer(pretty=True), measurements, {"linked", "clean"}
    )

    assert "✓" in output
    assert "✗" in output
    assert "boolean" not in output
