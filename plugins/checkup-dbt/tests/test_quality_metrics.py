from pathlib import Path

from checkup_dbt import (
    DbtFlaggedPackagesMetric,
    DbtModelsNotAdheringToNamingConventionMetric,
    DbtProfileHostMetric,
    DbtSupportedVersionMetric,
    DbtVersionMetric,
)
from checkup_dbt.provider import DbtManifestProvider

from checkup.hub import CheckHub

from .conftest import fact_dim_naming_checker, internal_model_naming_checker


def test_naming_convention_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics(
            [
                DbtModelsNotAdheringToNamingConventionMetric(
                    checker=internal_model_naming_checker
                )
            ]
        )
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_models_not_adhering_to_naming_convention"
    assert measurement.value == 0


def test_naming_convention_metric_custom_checker(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics(
            [
                DbtModelsNotAdheringToNamingConventionMetric(
                    checker=fact_dim_naming_checker
                )
            ]
        )
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert len(result.errors) == 0, f"Errors: {result.errors}"
    assert len(result.measurements) == 1

    measurement = result.measurements[0]
    assert measurement.value == 3


class Dbt19SupportedVersionMetric(DbtSupportedVersionMetric):
    min_version: str = "1.9"


def test_supported_version_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([Dbt19SupportedVersionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = next(
        m for m in result.measurements if m.metric.name == "dbt_supported_version"
    )
    assert measurement.metric.unit == "boolean"
    assert measurement.value == 1


def test_supported_version_metric_requires_min_version():
    """Test that DbtSupportedVersionMetric requires min_version to be configured."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DbtSupportedVersionMetric()


def test_version_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtVersionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_version"
    assert measurement.metric.unit == "version"
    assert measurement.value is not None
    assert isinstance(measurement.value, str)


class FlaggedPackageMetric(DbtFlaggedPackagesMetric):
    flagged_packages: list[str] = ["https://github.com/example/flagged-package"]


def test_flagged_packages_metric(sample_manifest_path_with_git_packages: Path):
    result = (
        CheckHub()
        .with_metrics([FlaggedPackageMetric()])
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

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_flagged_packages"
    assert measurement.metric.unit == "packages"
    assert measurement.value == 1
    assert "flagged-package" in measurement.diagnostic


class NoFlaggedPackageMetric(DbtFlaggedPackagesMetric):
    flagged_packages: list[str] = ["https://github.com/example/nonexistent"]


def test_flagged_packages_metric_no_matches(
    sample_manifest_path_with_git_packages: Path,
):
    result = (
        CheckHub()
        .with_metrics([NoFlaggedPackageMetric()])
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

    measurement = result.measurements[0]
    assert measurement.value == 0
    assert not measurement.diagnostic


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
        .with_metrics([DevProfileHostMetric()])
        .with_providers(
            [[DbtManifestProvider(manifest_path=sample_manifest_path_with_host)]]
        )
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_profile_host"
    assert measurement.metric.unit == "url"
    assert measurement.value == "myprefix.minerva.dp-ond.vlaanderen.be"


class ProdProfileHostMetric(DbtProfileHostMetric):
    target: str = "prod"


def test_profile_host_metric_prod(sample_manifest_path_with_host: Path):
    result = (
        CheckHub()
        .with_metrics([ProdProfileHostMetric()])
        .with_providers(
            [[DbtManifestProvider(manifest_path=sample_manifest_path_with_host)]]
        )
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.value == "prod.example.com"


def test_profile_host_metric_no_host(sample_manifest_path: Path):
    """Test when profiles.yml has no host configured."""
    result = (
        CheckHub()
        .with_metrics([DevProfileHostMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.value is None
    assert "No host found" in measurement.diagnostic


def test_profile_host_metric_requires_target():
    """Test that DbtProfileHostMetric requires target to be configured."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DbtProfileHostMetric()
