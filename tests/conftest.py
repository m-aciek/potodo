from contextlib import suppress
from pathlib import Path

import pytest

from potodo.potodo import main


@pytest.fixture(name="repo_dir")
def _repo_dir():
    return Path(__file__).resolve().parent / "fixtures" / "repository"


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
