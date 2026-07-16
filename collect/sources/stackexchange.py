"""Stack Exchange. The no-accepted-answer filter is the point: an unsolved
question is a stated problem nobody has fixed."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from collect.models import Item

API = "https://api.stackexchange.com/2.3/questions/unanswered"
TIMEOUT = httpx.Timeout(20.0)
SITES = ("stackoverflow", "superuser", "serverfault")


def fetch_stackexchange(pages: int = 2) -> list[Item]:
    items: list[Item] = []
    with httpx.Client(timeout=TIMEOUT) as client:
        for site in SITES:
            for page in range(1, pages + 1):
                resp = client.get(
                    API,
                    params={
                        "site": site,
                        "page": page,
                        "pagesize": 100,
                        "order": "desc",
                        "sort": "creation",
                        "filter": "!nNPvSNdWme",  # includes body_markdown
                    },
                )
                resp.raise_for_status()
                payload = resp.json()
                for q in payload.get("items", []):
                    items.append(
                        Item(
                            source="stackexchange",
                            id=f"{site}:{q['question_id']}",
                            url=q["link"],
                            title=q["title"],
                            body=q.get("body_markdown", "")[:4000],
                            created_utc=datetime.fromtimestamp(
                                q["creation_date"], tz=timezone.utc
                            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            engagement=int(q.get("score") or 0),
                        )
                    )
                if not payload.get("has_more"):
                    break
    return items
