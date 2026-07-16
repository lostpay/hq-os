"""One module per API. One API changing shape touches exactly one file."""

from collections.abc import Callable

from collect.models import Item
from collect.sources.bluesky import fetch_bluesky
from collect.sources.github_issues import fetch_github_issues
from collect.sources.hackernews import fetch_hackernews
from collect.sources.reddit import MissingCredential, fetch_reddit
from collect.sources.rss import fetch_rss
from collect.sources.stackexchange import fetch_stackexchange

SOURCES: dict[str, Callable[[], list[Item]]] = {
    "hackernews": fetch_hackernews,
    "stackexchange": fetch_stackexchange,
    "rss": fetch_rss,
    "reddit": fetch_reddit,
    "bluesky": fetch_bluesky,
    "github": fetch_github_issues,
}

__all__ = [
    "SOURCES",
    "MissingCredential",
    "fetch_bluesky",
    "fetch_github_issues",
    "fetch_hackernews",
    "fetch_reddit",
    "fetch_rss",
    "fetch_stackexchange",
]
