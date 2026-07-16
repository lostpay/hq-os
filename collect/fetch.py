"""Fail loudly: one source dying never takes the run with it."""

from __future__ import annotations

import logging
from collections.abc import Callable

from collect.models import Item, SourceResult

log = logging.getLogger(__name__)


def fetch_safely(name: str, fn: Callable[[], list[Item]]) -> SourceResult:
    """Run a source, isolating any failure into the result.

    Never raises. A source that returns zero items without erroring is flagged
    `zero_yield` — that is the case that would otherwise let a routine conclude
    "no problems today" from a silently broken scraper.
    """
    try:
        items = fn()
    except Exception as exc:  # noqa: BLE001 — isolation is the entire point
        log.error("source %s failed: %s: %s", name, type(exc).__name__, exc)
        return SourceResult(
            name=name, items=[], error=f"{type(exc).__name__}: {exc}", zero_yield=False
        )

    if not items:
        log.warning("source %s returned zero items without erroring", name)
        return SourceResult(name=name, items=[], error=None, zero_yield=True)

    log.info("source %s returned %d items", name, len(items))
    return SourceResult(name=name, items=items, error=None, zero_yield=False)
