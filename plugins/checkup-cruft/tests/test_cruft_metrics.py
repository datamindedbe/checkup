from pathlib import Path

from checkup_cruft import (
    CruftCommitsBehindMetric,
    CruftConflictCountMetric,
    CruftDaysBehindTemplateMetric,
    CruftDaysSinceUpdateMetric,
    CruftLinkedMetric,
    CruftProvider,
    CruftUpToDateMetric,
)

from checkup.hub import CheckHub


def _measure(repo: Path, metric, *, fetch_template: bool = False):
    result = (
        CheckHub()
        .with_metrics([metric])
        .with_providers(
            [[CruftProvider(project_path=repo, fetch_template=fetch_template)]]
        )
        .measure()
    )
    assert len(result.errors) == 0, f"Errors: {result.errors}"
    return next(m for m in result.measurements if m.metric.name == metric.name)


def test_linked_true(make_product, template_repo):
    repo = make_product(template_repo, "deadbeef")
    assert _measure(repo, CruftLinkedMetric()).value is True


def test_linked_false(make_product):
    repo = make_product()
    assert _measure(repo, CruftLinkedMetric()).value is False


def test_days_since_update_fresh(make_product, template_repo):
    repo = make_product(template_repo, "deadbeef")
    assert _measure(repo, CruftDaysSinceUpdateMetric()).value == 0


def test_days_since_update_none_without_cruft(make_product):
    repo = make_product()
    assert _measure(repo, CruftDaysSinceUpdateMetric()).value is None


def test_conflicts_counted(make_product, template_repo):
    repo = make_product(template_repo, "deadbeef", conflicts=2)
    measurement = _measure(repo, CruftConflictCountMetric())
    assert measurement.value == 2
    assert ".rej" in measurement.diagnostic


def test_no_conflicts(make_product, template_repo):
    repo = make_product(template_repo, "deadbeef")
    assert _measure(repo, CruftConflictCountMetric()).value == 0


def test_conflicts_finds_untracked_and_skips_gitignored(make_product, template_repo):
    repo = make_product(template_repo, "deadbeef")
    (repo / "model.sql.rej").write_text("x")  # untracked, must count
    (repo / ".gitignore").write_text("node_modules/\n")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "dep.rej").write_text("x")  # ignored, must not count
    measurement = _measure(repo, CruftConflictCountMetric())
    assert measurement.value == 1
    assert "model.sql.rej" in measurement.diagnostic


def _first_commit(repo: Path) -> str:
    import subprocess

    return subprocess.run(
        ["git", "-C", str(repo), "rev-list", "--max-parents=0", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_commits_behind(make_product, template_repo):
    pinned = _first_commit(template_repo)  # three commits total -> 2 behind
    repo = make_product(template_repo, pinned)
    assert _measure(repo, CruftCommitsBehindMetric(), fetch_template=True).value == 2


def test_up_to_date_when_pinned_to_head(make_product, template_repo):
    import subprocess

    head = subprocess.run(
        ["git", "-C", str(template_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    repo = make_product(template_repo, head)
    assert _measure(repo, CruftUpToDateMetric(), fetch_template=True).value is True


def test_up_to_date_false_when_behind(make_product, template_repo):
    repo = make_product(template_repo, _first_commit(template_repo))
    assert _measure(repo, CruftUpToDateMetric(), fetch_template=True).value is False


def test_days_behind_template(make_product, template_repo):
    # first commit 2020-01-01, head 2022-01-01 -> ~730 days
    repo = make_product(template_repo, _first_commit(template_repo))
    value = _measure(repo, CruftDaysBehindTemplateMetric(), fetch_template=True).value
    assert value >= 700


def test_drift_none_without_fetch(make_product, template_repo):
    repo = make_product(template_repo, _first_commit(template_repo))
    assert (
        _measure(repo, CruftCommitsBehindMetric(), fetch_template=False).value is None
    )
