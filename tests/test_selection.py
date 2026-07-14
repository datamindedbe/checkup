import pytest

from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.selection import select_metrics
from checkup.types import Context


class _FakeMetric(Metric):
    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        return self.measure(value=1)


def _metrics() -> list[Metric]:
    return [
        _FakeMetric(name="healthcheck_code_in_monorepo", tags=["healthcheck"]),
        _FakeMetric(name="healthcheck_cruft_linked", tags=["healthcheck"]),
        _FakeMetric(name="git_tracked_file_count", tags=["git"]),
        _FakeMetric(name="dbt_supported_version"),
    ]


_TYPE_RESOLVER = {
    "healthcheck_code_in_monorepo": "healthcheck_code_in_monorepo",
    "healthcheck_cruft_linked": "healthcheck_cruft_linked",
    "git_tracked_file_count": "git_tracked_file_count",
    "dbt_supported_version": "dbt_supported_version",
}


def _select(select=None, exclude=None):
    return select_metrics(
        _metrics(),
        select=select,
        exclude=exclude,
        type_resolver=lambda m: _TYPE_RESOLVER.get(m.name),
    )


def test_no_selector_includes_everything():
    assert _select() == {
        "healthcheck_code_in_monorepo",
        "healthcheck_cruft_linked",
        "git_tracked_file_count",
        "dbt_supported_version",
    }


def test_name_wildcard_is_the_default_method():
    assert _select("healthcheck_*") == {
        "healthcheck_code_in_monorepo",
        "healthcheck_cruft_linked",
    }
    assert _select("name:healthcheck_*") == _select("healthcheck_*")


def test_tag_method():
    assert _select("tag:healthcheck") == {
        "healthcheck_code_in_monorepo",
        "healthcheck_cruft_linked",
    }


def test_type_method():
    assert _select("type:git_tracked_file_count") == {"git_tracked_file_count"}


def test_union_of_atoms():
    assert _select("tag:git tag:healthcheck") == {
        "healthcheck_code_in_monorepo",
        "healthcheck_cruft_linked",
        "git_tracked_file_count",
    }


def test_exclude_removes_from_selection():
    assert _select(select="*", exclude="tag:healthcheck") == {
        "git_tracked_file_count",
        "dbt_supported_version",
    }


def test_exclude_without_select_applies_to_all():
    assert _select(exclude="healthcheck_*") == {
        "git_tracked_file_count",
        "dbt_supported_version",
    }


def test_exact_name_match():
    assert _select("dbt_supported_version") == {"dbt_supported_version"}


def test_unknown_method_raises():
    with pytest.raises(ValueError):
        _select("nope:healthcheck")
