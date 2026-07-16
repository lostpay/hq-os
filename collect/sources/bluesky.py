"""Bluesky via the free AT Protocol. Replaces Twitter at $0."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

from collect.models import Item
from collect.sources.reddit import MissingCredential

PDS = "https://bsky.social"
APPVIEW = "https://public.api.bsky.app"
TIMEOUT = httpx.Timeout(20.0)

QUERIES = [
    "i wish there was",
    "is there a tool that",
    "i have to manually",
    "the workaround is",
    "am i the only one who",
]


def _session(client: httpx.Client) -> str:
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        raise MissingCredential("BLUESKY_HANDLE / BLUESKY_APP_PASSWORD not set")

    resp = client.post(
        f"{PDS}/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["accessJwt"]


def _iso(raw: str) -> str:
    return (
        datetime.fromisoformat(raw.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def fetch_bluesky(queries: list[str] | None = None, limit: int = 100) -> list[Item]:
    items: list[Item] = []
    with httpx.Client(timeout=TIMEOUT) as client:
        jwt = _session(client)
        headers = {"Authorization": f"Bearer {jwt}"}

        for q in queries or QUERIES:
            resp = client.get(
                f"{APPVIEW}/xrpc/app.bsky.feed.searchPosts",
                params={"q": q, "limit": limit, "sort": "latest"},
                headers=headers,
            )
            resp.raise_for_status()
            for post in resp.json().get("posts", []):
                rkey = post["uri"].rsplit("/", 1)[-1]
                handle = post["author"]["handle"]
                text = post["record"]["text"]
                items.append(
                    Item(
                        source="bluesky",
                        id=post["uri"],
                        url=f"https://bsky.app/profile/{handle}/post/{rkey}",
                        title=text[:120],
                        body=text,
                        created_utc=_iso(post["record"]["createdAt"]),
                        engagement=int(post.get("likeCount") or 0),
                    )
                )
    return items
