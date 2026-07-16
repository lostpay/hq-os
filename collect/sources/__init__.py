"""One module per API. One API changing shape touches exactly one file."""

from collections.abc import Callable

from collect.models import Item
from collect.sources.hackernews import fetch_hackernews
from collect.sources.rss import fetch_rss
from collect.sources.stackexchange import fetch_stackexchange

SOURCES: dict[str, Callable[[], list[Item]]] = {
    "hackernews": fetch_hackernews,
    "stackexchange": fetch_stackexchange,
    "rss": fetch_rss,
}

__all__ = ["SOURCES", "fetch_hackernews", "fetch_rss", "fetch_stackexchange"]
