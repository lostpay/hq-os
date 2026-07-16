import json
from pathlib import Path

import httpx
import pytest
import respx

from collect.sources.hackernews import fetch_hackernews
from collect.sources.rss import fetch_rss
from collect.sources.stackexchange import fetch_stackexchange

FIXTURES = Path(__file__).parent / "fixtures"


@respx.mock
def test_hackernews_maps_algolia_hits_to_items():
    respx.get(url__startswith="https://hn.algolia.com/api/v1/search").mock(
        return_value=httpx.Response(200, json=json.loads((FIXTURES / "hn_algolia.json").read_text()))
    )
    items = fetch_hackernews()

    assert len(items) == 2
    first = items[0]
    assert first.source == "hackernews"
    assert first.id == "40001"
    assert first.url == "https://news.ycombinator.com/item?id=40001"
    assert "I have to manually" in first.text
    assert first.engagement == 12
    assert first.created_utc == "2026-07-15T09:00:00Z"


@respx.mock
def test_stackexchange_requests_only_unanswered_questions():
    route = respx.get(url__startswith="https://api.stackexchange.com/2.3/questions").mock(
        return_value=httpx.Response(200, json=json.loads((FIXTURES / "stackexchange.json").read_text()))
    )
    items = fetch_stackexchange()

    # No-accepted-answer is the whole point: an unsolved question is a stated
    # problem nobody has fixed. Answered questions are solved problems.
    called = str(route.calls[0].request.url)
    assert "unanswered" in called or "hasaccepted=False" in called.replace(" ", "")
    assert items[0].source == "stackexchange"
    assert items[0].engagement == 4


@respx.mock
def test_rss_maps_entries_to_items():
    respx.get(url__startswith="https://").mock(
        return_value=httpx.Response(200, text=(FIXTURES / "feed.xml").read_text())
    )
    items = fetch_rss(feeds=["https://example.com/feed.xml"])

    assert items[0].source == "rss"
    assert items[0].title == "Anthropic ships a new model"
    assert items[0].engagement == 0  # feeds carry no engagement signal


@respx.mock
def test_source_failure_raises_so_fetch_safely_can_catch_it():
    respx.get(url__startswith="https://hn.algolia.com").mock(
        return_value=httpx.Response(500, text="upstream error")
    )
    # Sources raise; only fetch_safely swallows. A source must never return []
    # on an error and disguise a breakage as a quiet day.
    with pytest.raises(httpx.HTTPStatusError):
        fetch_hackernews()
