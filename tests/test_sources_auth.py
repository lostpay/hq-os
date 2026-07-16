import json
from pathlib import Path

import httpx
import pytest
import respx

from collect.sources.bluesky import fetch_bluesky
from collect.sources.github_issues import fetch_github_issues
from collect.sources.reddit import MissingCredential, fetch_reddit

FIXTURES = Path(__file__).parent / "fixtures"


@respx.mock
def test_reddit_authenticates_then_maps_listing(monkeypatch):
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")

    token = respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    respx.get(url__startswith="https://oauth.reddit.com").mock(
        return_value=httpx.Response(
            200, json=json.loads((FIXTURES / "reddit_listing.json").read_text())
        )
    )

    items = fetch_reddit(subreddits=["devops"])

    assert token.called, "must use OAuth — anonymous reddit is 403 from datacenter IPs"
    assert items[0].source == "reddit"
    assert items[0].id == "t3_abc123"
    assert items[0].url == "https://www.reddit.com/r/devops/comments/abc123/every_time_i_deploy/"
    assert items[0].engagement == 12
    assert "every time i" in items[0].text.lower()


def test_reddit_without_credentials_raises_rather_than_returning_empty(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    # Returning [] here would be indistinguishable from "reddit had nothing today".
    with pytest.raises(MissingCredential):
        fetch_reddit(subreddits=["devops"])


@respx.mock
def test_bluesky_maps_posts(monkeypatch):
    monkeypatch.setenv("BLUESKY_HANDLE", "me.bsky.social")
    monkeypatch.setenv("BLUESKY_APP_PASSWORD", "pw")

    respx.post(url__regex=r"com\.atproto\.server\.createSession").mock(
        return_value=httpx.Response(200, json={"accessJwt": "jwt", "did": "did:plc:x"})
    )
    respx.get(url__regex=r"searchPosts").mock(
        return_value=httpx.Response(
            200, json=json.loads((FIXTURES / "bluesky_search.json").read_text())
        )
    )

    items = fetch_bluesky(queries=["i wish there was"])
    assert items[0].source == "bluesky"
    assert items[0].url == "https://bsky.app/profile/someone.bsky.social/post/xyz789"
    assert items[0].engagement == 2


@respx.mock
def test_github_issues_maps_feature_requests(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "tok")
    respx.get(url__startswith="https://api.github.com/search/issues").mock(
        return_value=httpx.Response(
            200, json=json.loads((FIXTURES / "github_issues.json").read_text())
        )
    )

    items = fetch_github_issues()
    assert items[0].source == "github"
    assert items[0].url == "https://github.com/example/repo/issues/412"
    assert items[0].engagement == 7  # reactions: recorded, never gated
