"""Reddit via free script-app OAuth.

Anonymous access to reddit.com/*.json is blocked from datacenter IPs — it works on a
laptop and 403s from an Actions runner. OAuth is not optional here.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx

from collect.models import Item

log = logging.getLogger(__name__)

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"
UA = "hq-collect/0.1 (personal problem-mining pipeline)"
TIMEOUT = httpx.Timeout(20.0)

SUBREDDITS = [
    "devops", "sysadmin", "webdev", "dataengineering", "selfhosted",
    "smallbusiness", "excel", "productivity", "freelance", "msp",
]


class MissingCredential(RuntimeError):
    """Raised rather than returning [] — a missing key must look like a failure,
    not like a quiet day."""


def _token(client: httpx.Client) -> str:
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        raise MissingCredential("REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set")

    resp = client.post(
        TOKEN_URL,
        auth=(cid, secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": UA},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_reddit(subreddits: list[str] | None = None, limit: int = 100) -> list[Item]:
    """Newest posts from each subreddit.

    `/new`, never `/top`. Top is a generic-problem detector.
    """
    items: list[Item] = []
    with httpx.Client(timeout=TIMEOUT) as client:
        token = _token(client)
        headers = {"Authorization": f"bearer {token}", "User-Agent": UA}

        for sub in subreddits or SUBREDDITS:
            resp = client.get(
                f"{API}/r/{sub}/new", params={"limit": limit}, headers=headers
            )
            resp.raise_for_status()
            for child in resp.json()["data"]["children"]:
                d = child["data"]
                items.append(
                    Item(
                        source="reddit",
                        id=d["name"],
                        url=f"https://www.reddit.com{d['permalink']}",
                        title=d.get("title", ""),
                        body=(d.get("selftext") or "")[:4000],
                        created_utc=datetime.fromtimestamp(
                            d["created_utc"], tz=timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        engagement=int(d.get("score") or 0),
                    )
                )
    return items
