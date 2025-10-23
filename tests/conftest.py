from contextlib import suppress
from pathlib import Path

import pytest

from potodo.potodo import main


@pytest.fixture(name="fixtures_dir")
def _fixtures_dir():
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(name="repo_dir")
def _repo_dir(fixtures_dir):
    return fixtures_dir / "repository"


@pytest.fixture(name="git_repo_dir")
def _git_repo_dir(fixtures_dir):
    return fixtures_dir / "git_repository"


@pytest.fixture
def run_potodo(repo_dir, capsys, monkeypatch):
    def run_it(argv):
        monkeypatch.setattr(
            "sys.argv", ["potodo", "--no-cache", "-p", str(repo_dir)] + argv
        )
        with suppress(SystemExit):
            main()
        return capsys.readouterr()

    return run_it
