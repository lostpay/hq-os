"""RSS: tech press and release notes. Feeds the you lens, not the problem lens —
news is not a stated problem."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import feedparser
import httpx

from collect.models import Item

TIMEOUT = httpx.Timeout(20.0)

DEFAULT_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://simonwillison.net/atom/everything/",
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://github.blog/changelog/feed/",
    "https://vercel.com/atom",
]


def _iso(entry) -> str:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def fetch_rss(feeds: list[str] | None = None) -> list[Item]:
    items: list[Item] = []
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        for url in feeds or DEFAULT_FEEDS:
            resp = client.get(url)
            resp.raise_for_status()
            for entry in feedparser.parse(resp.text).entries:
                items.append(
                    Item(
                        source="rss",
                        id=entry.get("id") or entry.get("link", ""),
                        url=entry.get("link", ""),
                        title=entry.get("title", ""),
                        body=(entry.get("summary") or "")[:4000],
                        created_utc=_iso(entry),
                        engagement=0,
                    )
                )
    return items
