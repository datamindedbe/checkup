from fixtures import DummyMetric, capture_output

from checkup.materializers import MarkdownMaterializer


def test_markdown_materializer_renders_table():
    """
    Markdown materializer emits a markdown table with header, separator and rows.
    """

    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42)

    output = capture_output(MarkdownMaterializer(), [measurement], {"dummy"})

    assert "| Name | Description | Value | Unit | Diagnostics |" in output
    assert "| --- | --- | ---: | --- | --- |" in output  # Value right-aligned
    assert "| dummy | Test metric | 42 | count |" in output


def test_markdown_materializer_escapes_pipes_and_newlines():
    """
    Cells cannot hold raw pipes or newlines; they must be escaped.
    """

    metric = DummyMetric(expected_value=1)
    measurement = metric.measure(value=1, diagnostic="a|b\nc")

    output = capture_output(MarkdownMaterializer(), [measurement], {"dummy"})

    assert "a\\|b<br>c" in output
    assert "a|b\nc" not in output


def test_markdown_pretty_formats_values():
    """
    Pretty mode folds units into the value and drops the Unit column.
    """

    measurements = [
        DummyMetric(name="linked", unit="boolean").measure(value=True),
        DummyMetric(name="clean", unit="boolean").measure(value=False),
        DummyMetric(name="coverage", unit="percent").measure(value=73),
        DummyMetric(name="models", unit="models").measure(value=5),
        DummyMetric(name="version", unit="version").measure(value="1.9.4"),
        DummyMetric(name="missing", unit="boolean").measure(value=None),
    ]
    direct = {m.metric.name for m in measurements}

    output = capture_output(MarkdownMaterializer(pretty=True), measurements, direct)

    assert "| Name | Description | Value | Diagnostics |" in output
    assert "Unit" not in output
    assert "| ✓ |" in output
    assert "| ✗ |" in output
    assert "| 73% |" in output
    assert "| 5 models |" in output
    assert "| 1.9.4 |" in output  # Non-numeric value: unit is not appended.
    assert "None" not in output
    assert "boolean" not in output


def test_markdown_columns_select_and_order():
    """
    An explicit columns list selects columns verbatim, in the given order.
    """

    measurement = DummyMetric(expected_value=42).measure(value=42)

    output = capture_output(
        MarkdownMaterializer(pretty=True, columns=["value", "description", "unit"]),
        [measurement],
        {"dummy"},
    )

    # Explicit columns beat pretty's default unit drop.
    assert "| Value | Description | Unit |" in output
    assert "| 42 count | Test metric | count |" in output


def test_markdown_description_falls_back_to_name():
    """
    Hiding the name column must not leave rows without an identifier.
    """

    measurement = DummyMetric(name="anon", description="").measure(value=1)

    output = capture_output(
        MarkdownMaterializer(columns=["description", "value"]), [measurement], {"anon"}
    )

    assert "| anon | 1 |" in output
