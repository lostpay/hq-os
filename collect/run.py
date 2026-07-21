"""Entrypoint. One pull, read through as many lenses as asked for.

Raw never enters git: the pull lives in memory, and only lens output is written.
Every run writes a log naming which sources died and which triage tier it reached,
so a gap is visible in the repo rather than inferred from an absence.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date as date_cls
from pathlib import Path

from collect.fetch import fetch_safely
from collect.models import Item, RunLog, SourceResult
from collect.problem_lens import run_problem_lens
from collect.sources import SOURCES
from collect.you_lens import run_you_lens

log = logging.getLogger(__name__)

NEWS_K = 40


def pull() -> tuple[list[Item], list[SourceResult]]:
    """Every source, each isolated. One dead API never takes the run with it."""
    results = [fetch_safely(name, fn) for name, fn in SOURCES.items()]
    items = [item for r in results for item in r.items]
    log.info("pulled %d items from %d sources", len(items), len(results))
    return items, results


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )
    log.info("wrote %d rows to %s", len(rows), path)


def do_problem_lens(
    items: list[Item], results: list[SourceResult], data_dir: Path, date: str
) -> None:
    run_log = RunLog(date=date, lens="problem", sources=results)
    kept = run_problem_lens(items, ideas_dir=data_dir / "ideas", log_=run_log)

    _write_jsonl(
        data_dir / "sources" / f"candidates-{date}.jsonl",
        [{**v.item.to_dict(), "why": v.why} for v in kept],
    )
    (data_dir / "sources" / f"run-{date}-problem.md").write_text(
        run_log.to_markdown(), encoding="utf-8"
    )


def do_you_lens(
    items: list[Item], results: list[SourceResult], data_dir: Path, date: str
) -> None:
    run_log = RunLog(date=date, lens="you", sources=results)
    profile = (data_dir / "profile.md").read_text(encoding="utf-8")
    ranked = run_you_lens(items, profile, log_=run_log, k=NEWS_K)

    _write_jsonl(
        data_dir / "sources" / f"news-{date}.jsonl",
        [{**item.to_dict(), "relevance": round(score, 4)} for item, score in ranked],
    )
    (data_dir / "sources" / f"run-{date}-you.md").write_text(
        run_log.to_markdown(), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="collect")
    parser.add_argument("--lens", choices=("problem", "you", "both"), default="both")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--date", default=date_cls.today().isoformat())
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    items, results = pull()

    if args.lens in ("problem", "both"):
        do_problem_lens(items, results, args.data_dir, args.date)
    if args.lens in ("you", "both"):
        do_you_lens(items, results, args.data_dir, args.date)

    return 0


if __name__ == "__main__":
    sys.exit(main())
