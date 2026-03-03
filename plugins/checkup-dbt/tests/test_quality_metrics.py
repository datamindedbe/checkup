from pathlib import Path

from checkup_dbt import (
    DbtFlaggedPackagesMetric,
    DbtProfileHostMetric,
    DbtSupportedVersionMetric,
    DbtVersionMetric,
)
from checkup_dbt.provider import DbtManifestProvider

from checkup.hub import CheckHub

from .conftest import FactDimNamingMetric, InternalModelNamingMetric


def test_naming_convention_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([InternalModelNamingMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_models_not_adhering_to_naming_convention"
    assert metric.value == 0


def test_naming_convention_metric_custom_checker(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([FactDimNamingMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert len(result.errors) == 0, f"Errors: {result.errors}"
    assert len(result.metrics) == 1

    metric = result.metrics[0]
    assert metric.value == 3


class Dbt19SupportedVersionMetric(DbtSupportedVersionMetric):
    min_version: str = "1.9"


def test_supported_version_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([Dbt19SupportedVersionMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = next(m for m in result.metrics if m.name == "dbt_supported_version")
    assert metric.unit == "boolean"
    assert metric.value == 1


def test_supported_version_metric_requires_min_version():
    """Test that DbtSupportedVersionMetric requires min_version to be configured."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DbtSupportedVersionMetric()


def test_version_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtVersionMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_version"
    assert metric.unit == "version"
    assert metric.value is not None
    assert isinstance(metric.value, str)


class FlaggedPackageMetric(DbtFlaggedPackagesMetric):
    flagged_packages: list[str] = ["https://github.com/example/flagged-package"]


def test_flagged_packages_metric(sample_manifest_path_with_git_packages: Path):
    result = (
        CheckHub()
        .with_metrics([FlaggedPackageMetric])
        .with_providers(
            [
                [
                    DbtManifestProvider(
                        manifest_path=sample_manifest_path_with_git_packages
                    )
                ]
            ]
        )
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_flagged_packages"
    assert metric.unit == "packages"
    assert metric.value == 1
    assert "flagged-package" in metric.diagnostic


class NoFlaggedPackageMetric(DbtFlaggedPackagesMetric):
    flagged_packages: list[str] = ["https://github.com/example/nonexistent"]


def test_flagged_packages_metric_no_matches(
    sample_manifest_path_with_git_packages: Path,
):
    result = (
        CheckHub()
        .with_metrics([NoFlaggedPackageMetric])
        .with_providers(
            [
                [
                    DbtManifestProvider(
                        manifest_path=sample_manifest_path_with_git_packages
                    )
                ]
            ]
        )
        .measure()
    )

    metric = result.metrics[0]
    assert metric.value == 0
    assert not metric.diagnostic


def test_flagged_packages_metric_requires_flagged_packages():
    """Test that DbtFlaggedPackagesMetric requires flagged_packages to be configured."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DbtFlaggedPackagesMetric()


class DevProfileHostMetric(DbtProfileHostMetric):
    target: str = "dev"


def test_profile_host_metric_dev(sample_manifest_path_with_host: Path):
    result = (
        CheckHub()
        .with_metrics([DevProfileHostMetric])
        .with_providers(
            [[DbtManifestProvider(manifest_path=sample_manifest_path_with_host)]]
        )
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_profile_host"
    assert metric.unit == "url"
    assert metric.value == "myprefix.minerva.dp-ond.vlaanderen.be"


class ProdProfileHostMetric(DbtProfileHostMetric):
    target: str = "prod"


def test_profile_host_metric_prod(sample_manifest_path_with_host: Path):
    result = (
        CheckHub()
        .with_metrics([ProdProfileHostMetric])
        .with_providers(
            [[DbtManifestProvider(manifest_path=sample_manifest_path_with_host)]]
        )
        .measure()
    )

    metric = result.metrics[0]
    assert metric.value == "prod.example.com"


def test_profile_host_metric_no_host(sample_manifest_path: Path):
    """Test when profiles.yml has no host configured."""
    result = (
        CheckHub()
        .with_metrics([DevProfileHostMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.value is None
    assert "No host found" in metric.diagnostic


def test_profile_host_metric_requires_target():
    """Test that DbtProfileHostMetric requires target to be configured."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DbtProfileHostMetric()
