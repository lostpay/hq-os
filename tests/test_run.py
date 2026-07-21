import json
from pathlib import Path

import pytest

from collect.models import Item
from collect.run import main


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    (tmp_path / "sources").mkdir()
    (tmp_path / "ideas" / "archive").mkdir(parents=True)
    (tmp_path / "ideas" / "mine.md").write_text("# mine\n")
    (tmp_path / "ideas" / "others.md").write_text("# others\n")
    (tmp_path / "profile.md").write_text(
        "# profile\n\n## Skills\nI ship backend Python and deploy on Vercel.\n"
    )
    return tmp_path


def _fake_sources(monkeypatch, items: list[Item]):
    monkeypatch.setattr("collect.run.SOURCES", {"fake": lambda: items})


def test_problem_lens_writes_candidates_and_a_run_log(data_dir, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _fake_sources(monkeypatch, [
        Item("fake", "1", "https://example.com/1", "I have to manually tag releases",
             "", "2026-07-16T00:00:00Z", 2),
        Item("fake", "2", "https://example.com/2", "Announcing version 9",
             "", "2026-07-16T00:00:00Z", 900),
    ])

    main(["--lens", "problem", "--data-dir", str(data_dir), "--date", "2026-07-16"])

    out = data_dir / "sources" / "candidates-2026-07-16.jsonl"
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["id"] == "1"
    assert rows[0]["why"]  # the triage reason travels with the candidate
    assert rows[0]["engagement"] == 2

    log = (data_dir / "sources" / "run-2026-07-16-problem.md").read_text()
    assert "Triage tier: **none**" in log
    assert "| raw | 2 |" in log


def test_you_lens_writes_news(data_dir, monkeypatch):
    _fake_sources(monkeypatch, [
        Item("fake", "1", "https://example.com/1", "Postgres 19 ships replication news",
             "", "2026-07-16T00:00:00Z", 0),
        Item("fake", "2", "https://example.com/2", "Competitive sourdough results",
             "", "2026-07-16T00:00:00Z", 0),
    ])

    main(["--lens", "you", "--data-dir", str(data_dir), "--date", "2026-07-16"])

    rows = [
        json.loads(line)
        for line in (data_dir / "sources" / "news-2026-07-16.jsonl").read_text().splitlines()
    ]
    assert rows[0]["id"] == "1"
    assert "relevance" in rows[0]
    assert not (data_dir / "sources" / "candidates-2026-07-16.jsonl").exists()


def test_raw_never_enters_the_output_dir(data_dir, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _fake_sources(monkeypatch, [
        Item("fake", str(i), f"https://example.com/{i}", "Announcing something",
             "", "2026-07-16T00:00:00Z", 0)
        for i in range(50)
    ])

    main(["--lens", "both", "--data-dir", str(data_dir), "--date", "2026-07-16"])

    written = {p.name for p in (data_dir / "sources").iterdir()}
    assert written == {
        "candidates-2026-07-16.jsonl",
        "news-2026-07-16.jsonl",
        "run-2026-07-16-problem.md",
        "run-2026-07-16-you.md",
    }
    # None of the 50 raw items survive the problem lens; the file exists but is empty.
    assert (data_dir / "sources" / "candidates-2026-07-16.jsonl").read_text() == ""


def test_a_dead_source_is_logged_and_the_run_still_completes(data_dir, monkeypatch):
    def boom() -> list[Item]:
        raise RuntimeError("API returned 500")

    good = Item("ok", "1", "https://example.com/1", "Postgres news",
                "", "2026-07-16T00:00:00Z", 0)
    monkeypatch.setattr("collect.run.SOURCES", {"dead": boom, "ok": lambda: [good]})

    main(["--lens", "you", "--data-dir", str(data_dir), "--date", "2026-07-16"])

    log = (data_dir / "sources" / "run-2026-07-16-you.md").read_text()
    assert "**FAILED**" in log
    assert "API returned 500" in log
    assert "## Gaps" in log
    assert (data_dir / "sources" / "news-2026-07-16.jsonl").read_text().strip()


def test_every_source_dead_still_writes_a_visible_stub(data_dir, monkeypatch):
    def boom() -> list[Item]:
        raise RuntimeError("everything is down")

    monkeypatch.setattr("collect.run.SOURCES", {"a": boom, "b": boom})

    main(["--lens", "you", "--data-dir", str(data_dir), "--date", "2026-07-16"])

    # The gap must be visible in the repo. A missing file is invisible; an empty
    # file plus a run log naming the failures is not.
    log = (data_dir / "sources" / "run-2026-07-16-you.md").read_text()
    assert log.count("**FAILED**") == 2
    assert (data_dir / "sources" / "news-2026-07-16.jsonl").exists()
