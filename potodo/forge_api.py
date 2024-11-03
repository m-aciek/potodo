import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import requests

TIMEOUT_CONNECT_DEFAULT = 6
TIMEOUT_READ_DEFAULT = 60


def get_issue_reservations(api_url: str) -> Dict[str, Tuple[Any, Any]]:
    """Will get the repository name then request all the issues and put them in a dict"""

    logging.info("Getting issue reservations from %s", urlparse(api_url).hostname)
    issues: List[Dict[Any, Any]] = []
    logging.debug("Getting %s", api_url)
    next_url = api_url
    while next_url:
        logging.debug("Getting %s", next_url)
        resp = requests.get(
            next_url, timeout=(TIMEOUT_CONNECT_DEFAULT, TIMEOUT_READ_DEFAULT)
        )
        if resp.status_code == 403:
            # Rate limit exceeded
            return {}
        issues.extend(resp.json())
        next_url = resp.links.get("next", {}).get("url")

    resp = requests.get(
        api_url, timeout=(TIMEOUT_CONNECT_DEFAULT, TIMEOUT_READ_DEFAULT)
    )
    if resp.status_code == 403:
        # Rate limit exceeded
        return {}
    issues.extend(resp.json())
    logging.debug("Found %s issues", len(issues))

    reservations = {}
    api_uri_base = api_url.rsplit("/issues?", 1)[0]

    for issue in issues:
        # PR are also issues, but issues are not always PRs
        is_pull_request = issue["pull_request"] is not None
        if is_pull_request:
            number = issue["number"]
            pr_api_url = f"{api_uri_base}/pulls/{number}/files"
            resp = requests.get(
                pr_api_url, timeout=(TIMEOUT_CONNECT_DEFAULT, TIMEOUT_READ_DEFAULT)
            )
            if resp.status_code == 403:
                # Rate limit exceeded
                continue
            files = [
                x["filename"] for x in resp.json() if x["filename"].endswith(".po")
            ]
        else:
            # Maybe find a better way for not using python 3.8 ?
            files = re.findall(r"\w*/[\w\-\.]*\.po", issue["title"])

        if files:
            creation_date = datetime.strptime(
                issue["created_at"].split("T")[0], "%Y-%m-%d"
            ).date()
            user_login = issue["user"]["login"]
            reservations.update({file: (user_login, creation_date) for file in files})

    logging.debug("Found %s reservations", len(reservations))
    return reservations
