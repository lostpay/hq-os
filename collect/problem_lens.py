"""The problem lens: ~5,000 raw → ~300 phrase matches → ~50 candidates.

Three stages, cheapest first, each answering one question. None of them personal —
this lens must work identically for anyone, which is what makes it discovery rather
than a mirror.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from collect.embed import dedup
from collect.models import Item, RunLog
from collect.triage import Verdict, triage

log = logging.getLogger(__name__)

# The niche-finder. These phrases select for someone describing a workflow that is
# broken for them specifically — which is exactly what sorting by upvotes destroys.
PROBLEM_PHRASES = [
    r"i wish (?:there was|there were|i could|it could)",
    r"is there (?:a|any) (?:tool|app|way|service|library|plugin) (?:that|to)",
    r"i have to manually",
    r"every ?time i\b",
    r"the workaround is",
    r"am i the only one who",
    r"there(?:'s| is) no (?:easy |good |simple )?way to",
    r"why (?:is there no|isn'?t there)",
    r"i (?:keep|end up) (?:having to|doing this)",
    r"by hand every",
    r"would be nice if",
    r"anyone (?:know of|found) a (?:tool|way)",
    r"currently i (?:just |have to )?(?:copy|paste|re-?type|export)",
    r"drives me (?:crazy|mad|nuts)",
    r"spent (?:hours|all day) (?:trying to|manually)",
]

_PHRASE_RE = re.compile("|".join(PROBLEM_PHRASES), re.IGNORECASE)
_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)

DEDUP_THRESHOLD = 0.82


def matches_problem_phrase(text: str) -> bool:
    """Is someone stating a problem, rather than announcing or opining?"""
    return bool(_PHRASE_RE.search(text))


def existing_statements(ideas_dir: Path) -> list[str]:
    """Every problem statement already known: both lists plus the whole archive.

    The archive is included so a rejected idea does not come back every night wearing
    different words.
    """
    statements: list[str] = []
    for name in ("mine.md", "others.md"):
        path = ideas_dir / name
        if path.exists():
            statements += _H2_RE.findall(path.read_text(encoding="utf-8"))

    archive = ideas_dir / "archive"
    if archive.is_dir():
        for path in sorted(archive.glob("*.md")):
            statements += _H2_RE.findall(path.read_text(encoding="utf-8"))

    log.info("dedup corpus: %d known statements", len(statements))
    return statements


def run_problem_lens(items: list[Item], ideas_dir: Path, log_: RunLog) -> list[Verdict]:
    """regex → embed-dedup → free-model triage. Records the funnel on `log_`."""
    log_.counts["raw"] = len(items)

    phrased = [i for i in items if matches_problem_phrase(i.text)]
    log_.counts["after_phrase_filter"] = len(phrased)

    fresh, dropped = dedup(phrased, existing_statements(ideas_dir), DEDUP_THRESHOLD)
    log_.counts["after_dedup"] = len(fresh)
    log_.counts["dedup_dropped"] = dropped

    verdicts, tier = triage(fresh)
    log_.tier = tier

    kept = [v for v in verdicts if v.keep]
    log_.counts["triage_rejected"] = len(verdicts) - len(kept)
    log_.counts["kept"] = len(kept)

    log.info(
        "problem lens: %d raw → %d phrased → %d fresh → %d kept (tier=%s)",
        len(items), len(phrased), len(fresh), len(kept), tier,
    )
    return kept
