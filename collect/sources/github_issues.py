"""GitHub issues. A feature request is a stated unmet need with a name attached."""

from __future__ import annotations

import os
from datetime import date, timedelta

import httpx

from collect.models import Item
from collect.sources.reddit import MissingCredential

API = "https://api.github.com/search/issues"
TIMEOUT = httpx.Timeout(20.0)

QUERIES = [
    'label:"feature request" state:open created:>{since}',
    "label:enhancement state:open created:>{since} comments:>2",
    '"would be nice if" in:body state:open created:>{since}',
]


def fetch_github_issues(days: int = 3, per_page: int = 100) -> list[Item]:
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise MissingCredential("GH_TOKEN not set")

    since = (date.today() - timedelta(days=days)).isoformat()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    items: list[Item] = []
    with httpx.Client(timeout=TIMEOUT) as client:
        for template in QUERIES:
            resp = client.get(
                API,
                params={
                    "q": template.format(since=since),
                    "sort": "created",
                    "order": "desc",
                    "per_page": per_page,
                },
                headers=headers,
            )
            resp.raise_for_status()
            for issue in resp.json().get("items", []):
                items.append(
                    Item(
                        source="github",
                        id=str(issue["id"]),
                        url=issue["html_url"],
                        title=issue["title"],
                        body=(issue.get("body") or "")[:4000],
                        created_utc=issue["created_at"],
                        engagement=int(
                            (issue.get("reactions") or {}).get("total_count") or 0
                        ),
                    )
                )
    return items
