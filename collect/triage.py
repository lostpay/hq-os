"""The third stage of the problem lens: is this real, specific, and unsolved?

A ladder, not a dependency. Groq → OpenRouter → nothing. The bottom rung keeps
everything: regex and dedup have already run, so the output is blunter but real.
The run always completes, and always reports which rung it landed on.

Open-weight models on free hosts only. Max covers Claude Code sessions, not raw API
calls from an Action — routing this to a paid model would be a separate bill.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import NamedTuple

import httpx

from collect.models import Item

log = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(90.0)
BATCH = 25

PROMPT = """You are filtering posts to find STATED PROBLEMS worth solving with software.

For each item, decide keep=true only if ALL of these hold:
- REAL: someone is describing an actual problem they hit, not speculating or venting.
- SPECIFIC: you could name the broken workflow. "X is bad" is not specific.
- UNSOLVED: no obvious existing tool already does this.
- SOFTWARE-SOLVABLE: code could plausibly fix it.

Ignore how popular a post is. A post with 3 upvotes describing a precise broken
workflow is exactly what we want. A post with 3000 upvotes describing a problem
everyone already knows about is not.

Do NOT consider who is reading this or what they are good at. Relevance is not your job.

Return ONLY this JSON, no prose:
{"verdicts": [{"id": "<id>", "keep": true|false, "why": "<one clause>"}]}

Items:
"""


@dataclass(frozen=True)
class Verdict:
    item: Item
    keep: bool
    why: str


class Tier(NamedTuple):
    name: str
    url: str
    key_env: str
    model: str


# OpenRouter ID verified against the live model list (Task 9 Step 1). Groq's ID is
# a starting guess, deferred for live verification to Task 12 once GROQ_API_KEY is
# registered. Both rot fast — see rot.md.
TIERS: list[Tier] = [
    Tier(
        name="groq",
        url="https://api.groq.com/openai/v1/chat/completions",
        key_env="GROQ_API_KEY",
        model="llama-3.3-70b-versatile",
    ),
    Tier(
        name="openrouter",
        url="https://openrouter.ai/api/v1/chat/completions",
        key_env="OPENROUTER_API_KEY",
        model="meta-llama/llama-3.3-70b-instruct:free",
    ),
]


def _render(items: list[Item]) -> str:
    lines = []
    for item in items:
        body = item.body.replace("\n", " ")[:600]
        lines.append(f'- id={item.id} | {item.title} | {body}')
    return PROMPT + "\n".join(lines)


def _ask(tier: Tier, key: str, items: list[Item], client: httpx.Client) -> dict[str, dict]:
    resp = client.post(
        tier.url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": tier.model,
            "messages": [{"role": "user", "content": _render(items)}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return {str(v["id"]): v for v in parsed["verdicts"]}


def _try_tier(tier: Tier, items: list[Item]) -> dict[str, dict] | None:
    key = os.environ.get(tier.key_env)
    if not key:
        log.warning("tier %s: %s not set, skipping", tier.name, tier.key_env)
        return None

    merged: dict[str, dict] = {}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            for start in range(0, len(items), BATCH):
                merged |= _ask(tier, key, items[start : start + BATCH], client)
    except Exception as exc:  # noqa: BLE001 — any failure means fall down the ladder
        log.warning("tier %s failed: %s: %s", tier.name, type(exc).__name__, exc)
        return None
    return merged


def triage(items: list[Item]) -> tuple[list[Verdict], str]:
    """Judge items, returning verdicts and the tier actually used.

    An item the model did not judge is KEPT. Dropping it would delete a candidate
    because a model was sloppy, which is a silent loss — exactly what this OS is not
    allowed to do.
    """
    if not items:
        return [], "none"

    for tier in TIERS:
        judged = _try_tier(tier, items)
        if judged is None:
            continue
        log.info("triage: tier %s judged %d/%d", tier.name, len(judged), len(items))
        verdicts = []
        for item in items:
            v = judged.get(item.id)
            if v is None:
                verdicts.append(Verdict(item, True, "not judged by the model — kept"))
            else:
                verdicts.append(Verdict(item, bool(v["keep"]), str(v.get("why", ""))))
        return verdicts, tier.name

    log.error("all triage tiers unavailable — degrading to regex + dedup only")
    return (
        [Verdict(i, True, "no triage tier available — kept unjudged") for i in items],
        "none",
    )
