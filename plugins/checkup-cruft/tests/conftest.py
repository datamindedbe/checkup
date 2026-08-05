import json
import subprocess
from pathlib import Path

import pytest


def _git(repo: Path, *args: str, date: str | None = None) -> str:
    env = None
    if date:
        env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env={**_base_env(), **env} if env else None,
    )
    return result.stdout.strip()


def _base_env() -> dict[str, str]:
    import os

    return os.environ.copy()


def _commit(repo: Path, message: str, *, date: str | None = None) -> str:
    _git(repo, "add", ".")
    _git(
        repo,
        "-c",
        "user.email=t@t",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "-m",
        message,
        date=date,
    )
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def template_repo(tmp_path: Path) -> Path:
    """
    A local git repo standing in for a cruft template, with three commits.
    """

    repo = tmp_path / "template"
    repo.mkdir()
    _git(repo, "init", "-q")
    for i, date in enumerate(["2020-01-01", "2021-01-01", "2022-01-01"]):
        (repo / "file.txt").write_text(str(i))
        _commit(repo, f"c{i}", date=f"{date}T00:00:00")
    return repo


@pytest.fixture
def make_product(tmp_path: Path):
    """
    Build a product repo with a .cruft.json pinned to a given template commit.
    """

    def _make(
        template: Path | None = None,
        pinned: str | None = None,
        *,
        conflicts: int = 0,
        commit_cruft: bool = True,
    ) -> Path:
        repo = tmp_path / "product"
        repo.mkdir()
        _git(repo, "init", "-q")
        (repo / "readme.md").write_text("x")
        _commit(repo, "init")

        if template is not None:
            (repo / ".cruft.json").write_text(
                json.dumps(
                    {"template": str(template), "commit": pinned, "checkout": None}
                )
            )
            for n in range(conflicts):
                (repo / f"file{n}.py.rej").write_text("conflict")
            if commit_cruft:
                _commit(repo, "add cruft")
        return repo

    return _make
