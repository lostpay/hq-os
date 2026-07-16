from pathlib import Path

import pytest

from collect.models import Item, RunLog
from collect.problem_lens import (
    existing_statements,
    matches_problem_phrase,
    run_problem_lens,
)


def _item(i: int, title: str, body: str = "", engagement: int = 0) -> Item:
    return Item(
        source="test", id=str(i), url=f"https://example.com/{i}",
        title=title, body=body, created_utc="2026-07-16T00:00:00Z",
        engagement=engagement,
    )


@pytest.mark.parametrize("text", [
    "I wish there was a way to diff these",
    "Is there a tool that converts this?",
    "I have to manually copy each row",
    "Every time I deploy, the config resets",
    "The workaround is to restart it twice",
    "Am I the only one who finds this broken?",
    "IS THERE A TOOL THAT does this",  # case-insensitive
])
def test_problem_phrases_match(text):
    assert matches_problem_phrase(text)


@pytest.mark.parametrize("text", [
    "Announcing version 4 of our framework",
    "Show HN: I built a thing",
    "This library is great",
])
def test_non_problems_do_not_match(text):
    assert not matches_problem_phrase(text)


def test_existing_statements_reads_h2s_from_lists_and_archive(tmp_path: Path):
    (tmp_path / "archive").mkdir()
    (tmp_path / "mine.md").write_text(
        "# mine\n\nIntro prose.\n\n## Renaming exports by hand\n\nArgument here.\n"
    )
    (tmp_path / "others.md").write_text("# others\n\n## Terraform plans are unreadable\n")
    (tmp_path / "archive" / "2026-07-01.md").write_text(
        "# archive\n\n## A rejected problem about cron\n"
    )

    got = existing_statements(tmp_path)

    assert set(got) == {
        "Renaming exports by hand",
        "Terraform plans are unreadable",
        "A rejected problem about cron",
    }


def test_existing_statements_on_empty_dir_is_empty_not_an_error(tmp_path: Path):
    assert existing_statements(tmp_path) == []


def test_funnel_filters_by_phrase_then_dedups_then_triages(tmp_path, monkeypatch):
    (tmp_path / "mine.md").write_text("# mine\n\n## Renaming exports by hand every time\n")
    (tmp_path / "others.md").write_text("# others\n")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    items = [
        _item(1, "Announcing our new release"),                       # no phrase
        _item(2, "I have to manually rename every export by hand"),   # dupe of mine.md
        _item(3, "I wish there was a way to diff terraform plans"),   # survives
    ]
    log = RunLog(date="2026-07-16", lens="problem")
    kept = run_problem_lens(items, ideas_dir=tmp_path, log_=log)

    assert log.counts["raw"] == 3
    assert log.counts["after_phrase_filter"] == 2
    assert log.counts["after_dedup"] == 1
    assert log.counts["kept"] == 1
    assert log.tier == "none"
    assert [v.item.id for v in kept] == ["3"]


def test_engagement_is_never_a_gate(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    (tmp_path / "mine.md").write_text("# mine\n")

    items = [
        _item(1, "I have to manually tag each release", engagement=0),
        _item(2, "I wish there was a linter for this", engagement=4000),
    ]
    log = RunLog(date="2026-07-16", lens="problem")
    kept = run_problem_lens(items, ideas_dir=tmp_path, log_=log)

    # The 0-engagement item must survive exactly as readily as the 4000 one.
    assert {v.item.id for v in kept} == {"1", "2"}
