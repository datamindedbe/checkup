"""Integration tests for the full metrics pipeline."""
from checkup import CheckHub, CSVMaterializer
from conftest import IntegrationBaseMetric, IntegrationDerivedMetric, PathMetric


def test_full_pipeline(tmp_path):
    """Test complete pipeline: config, providers, dependencies, calculation, output."""
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  base_metric:
    threshold: 50
  derived_metric:
    multiplier: 3
""")

    result = (
        CheckHub(config_path=config_file)
        .with_metrics([IntegrationDerivedMetric])
        .measure()
    )

    assert len(result.metrics) == 2
    metrics_by_name = {m.name: m for m in result.metrics}

    assert metrics_by_name["base_metric"].is_direct is False
    assert metrics_by_name["base_metric"].value == 25
    assert metrics_by_name["base_metric"].threshold == 50

    assert metrics_by_name["derived_metric"].is_direct is True
    assert metrics_by_name["derived_metric"].value == 75  # 25 * 3
    assert metrics_by_name["derived_metric"].multiplier == 3


def test_full_pipeline_with_both_metrics(tmp_path):
    """Test complete pipeline when both metrics are requested."""
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  base_metric:
    threshold: 50
  derived_metric:
    multiplier: 3
""")

    result = (
        CheckHub(config_path=config_file)
        .with_metrics([IntegrationBaseMetric, IntegrationDerivedMetric])
        .measure()
    )

    metrics_by_name = {m.name: m for m in result.metrics}

    assert metrics_by_name["base_metric"].value == 25
    assert metrics_by_name["base_metric"].threshold == 50

    assert metrics_by_name["derived_metric"].value == 75  # 25 * 3
    assert metrics_by_name["derived_metric"].multiplier == 3


def test_multi_context_pipeline(tmp_path):
    """Test complete multi-context pipeline with config, providers, and materialization."""
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  path_metric:
    multiplier: 2
""")

    result = (
        CheckHub(config_path=config_file)
        .with_metrics([PathMetric])
        .with_contexts([
            {"path": "/short"},       # len=6, * 2 = 12
            {"path": "/medium/path"}, # len=12, * 2 = 24
            {"path": "/very/long/path/here"},  # len=20, * 2 = 40
        ])
        .measure(max_workers=2)
    )

    assert len(result.metrics) == 3
    assert len(result.errors) == 0

    metrics_by_path = {m.tags["path"]: m for m in result.metrics}

    assert metrics_by_path["/short"].value == 12
    assert metrics_by_path["/medium/path"].value == 24
    assert metrics_by_path["/very/long/path/here"].value == 40

    csv_path = tmp_path / "results.csv"
    result.materialize(CSVMaterializer(output_path=csv_path, include_indirect=True))

    content = csv_path.read_text()
    assert content.count("path_metric") == 3
    assert "12" in content
    assert "24" in content
    assert "40" in content
