"""The you lens: the same pull, read for relevance instead of for pain.

The problem-phrase regex strips news out entirely, so the briefing needs its own cut.
This is the only module in `collect` that reads profile.md — see the personalization
line in the kernel. Nothing here touches the problem lens, and idea-engine never
touches this.
"""

from __future__ import annotations

import logging

from collect.embed import top_against
from collect.models import Item, RunLog

log = logging.getLogger(__name__)

MIN_PROFILE_CHARS = 40


def run_you_lens(
    items: list[Item], profile_text: str, log_: RunLog, k: int = 40
) -> list[tuple[Item, float]]:
    """The k items closest to the profile, most similar first.

    Raises on an empty profile rather than returning an arbitrary k items: a lens that
    matches everything is indistinguishable from no lens, and it would be invisible in
    the output.
    """
    if len(profile_text.strip()) < MIN_PROFILE_CHARS:
        raise ValueError(
            f"profile is empty or near-empty ({len(profile_text.strip())} chars) — "
            "a vague profile makes a vague lens, an empty one makes no lens at all"
        )

    log_.counts["raw"] = len(items)
    ranked = top_against(items, profile_text, k)
    log_.counts["kept"] = len(ranked)

    log.info("you lens: %d raw → %d kept (k=%d)", len(items), len(ranked), k)
    return ranked
