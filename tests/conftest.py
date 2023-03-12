from pathlib import Path

import pytest


@pytest.fixture
def repo_dir():
    return Path(__file__).resolve().parent / "fixtures" / "repository"


@pytest.fixture
def base_config(repo_dir):
    def select(po_file) -> bool:
        """Return True if the po_file should be displayed, False otherwise."""
        return not (
            po_file.percent_translated == 100
            or po_file.percent_translated < 0
            or po_file.percent_translated > 100
        )

    return {
        "path": repo_dir,
        "exclude": ["excluded/", "excluded.po"],
        "hide_reserved": False,
        "counts": False,
        "json_format": False,
        "select": select,
        "show_reservation_dates": False,
        "no_cache": True,
        "is_interactive": False,
        "matching_files": False,
        "api_url": "",
    }
