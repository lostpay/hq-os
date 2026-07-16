"""Hacker News via Algolia. No auth, real point and comment counts."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from collect.models import Item

API = "https://hn.algolia.com/api/v1/search_by_date"
TIMEOUT = httpx.Timeout(20.0)


def _iso(raw: str) -> str:
    return (
        datetime.fromisoformat(raw.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def fetch_hackernews(hits: int = 400) -> list[Item]:
    """Recent stories and Ask HN posts.

    Sorted by date, never by points — see "the engagement trap". Points are recorded
    on the Item as secondary evidence only.
    """
    items: list[Item] = []
    with httpx.Client(timeout=TIMEOUT) as client:
        # "(story,ask_hn)" is Algolia's OR-grouping syntax for tags — one call
        # covering both post types, sorted by date via the search_by_date endpoint.
        resp = client.get(
            API,
            params={"tags": "(story,ask_hn)", "hitsPerPage": min(hits, 1000)},
        )
        resp.raise_for_status()
        for hit in resp.json()["hits"]:
            if not hit.get("title"):
                continue
            items.append(
                Item(
                    source="hackernews",
                    id=str(hit["objectID"]),
                    url=f"https://news.ycombinator.com/item?id={hit['objectID']}",
                    title=hit["title"],
                    body=hit.get("story_text") or hit.get("comment_text") or "",
                    created_utc=_iso(hit["created_at"]),
                    engagement=int(hit.get("points") or 0),
                )
            )
    return items
