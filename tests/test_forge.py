from datetime import date
from unittest.mock import patch

from potodo.forge_api import get_issue_reservations


class ResponseWithoutPullRequestProperty:
    """Mock response, mimicking github."""

    status_code = 200
    links = {}

    def json(self):
        return [
            {
                "title": "repository/file1.po",
                "created_at": "2024-01-01T12:00:00Z",
                "user": {"login": "user1"},
            }
        ]


def test_doesnt_fail_on_a_response_without_pull_request_property():
    with patch(
        "potodo.forge_api.requests.get",
        return_value=ResponseWithoutPullRequestProperty(),
    ):
        reservations = get_issue_reservations(
            "https://api.example.com/repos/ORGANISATION/REPOSITORY/issues?state=open"
        )
    assert reservations == {"repository/file1.po": ("user1", date(2024, 1, 1))}
