import httpx
import respx

from collect.models import Item
from collect.triage import triage


def _item(i: int, title: str) -> Item:
    return Item(
        source="test", id=str(i), url=f"https://example.com/{i}",
        title=title, body="", created_utc="2026-07-16T00:00:00Z", engagement=0,
    )


def _reply(verdicts: list[dict]) -> dict:
    import json
    return {"choices": [{"message": {"content": json.dumps({"verdicts": verdicts})}}]}


@respx.mock
def test_groq_is_tried_first_and_its_tier_is_reported(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")

    groq = respx.post(url__startswith="https://api.groq.com").mock(
        return_value=httpx.Response(200, json=_reply([
            {"id": "1", "keep": True, "why": "specific, unsolved, weekly"},
            {"id": "2", "keep": False, "why": "vague complaint, no stated problem"},
        ]))
    )
    verdicts, tier = triage([_item(1, "manual rename"), _item(2, "everything sucks")])

    assert groq.called
    assert tier == "groq"
    assert [v.keep for v in verdicts] == [True, False]
    assert verdicts[0].why == "specific, unsolved, weekly"


@respx.mock
def test_groq_rate_limit_falls_back_to_openrouter(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")

    respx.post(url__startswith="https://api.groq.com").mock(
        return_value=httpx.Response(429, text="rate limited")
    )
    orouter = respx.post(url__startswith="https://openrouter.ai").mock(
        return_value=httpx.Response(200, json=_reply([{"id": "1", "keep": True, "why": "ok"}]))
    )

    verdicts, tier = triage([_item(1, "manual rename")])

    assert orouter.called
    assert tier == "openrouter"
    assert verdicts[0].keep is True


@respx.mock
def test_both_tiers_down_degrades_to_keeping_everything(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")

    respx.post(url__startswith="https://api.groq.com").mock(
        return_value=httpx.Response(500, text="down")
    )
    respx.post(url__startswith="https://openrouter.ai").mock(
        return_value=httpx.Response(500, text="down")
    )

    verdicts, tier = triage([_item(1, "a"), _item(2, "b")])

    # The run always completes. Blunter, still works: regex and dedup already ran.
    assert tier == "none"
    assert len(verdicts) == 2
    assert all(v.keep for v in verdicts)
    assert all("no triage tier available" in v.why for v in verdicts)


def test_no_keys_at_all_degrades_without_touching_the_network(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    verdicts, tier = triage([_item(1, "a")])
    assert tier == "none"
    assert verdicts[0].keep is True


@respx.mock
def test_malformed_model_output_falls_through_rather_than_crashing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    respx.post(url__startswith="https://api.groq.com").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})
    )
    verdicts, tier = triage([_item(1, "a")])
    assert tier == "none"
    assert verdicts[0].keep is True


@respx.mock
def test_items_missing_from_the_reply_are_kept(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    respx.post(url__startswith="https://api.groq.com").mock(
        return_value=httpx.Response(200, json=_reply([{"id": "1", "keep": False, "why": "vague"}]))
    )
    # Item 2 was never judged. Dropping it silently would delete a candidate on a
    # model's sloppiness — keep it and say why.
    verdicts, tier = triage([_item(1, "a"), _item(2, "b")])
    assert tier == "groq"
    by_id = {v.item.id: v for v in verdicts}
    assert by_id["1"].keep is False
    assert by_id["2"].keep is True
    assert "not judged" in by_id["2"].why


@respx.mock
def test_verdict_missing_the_keep_field_does_not_crash_the_run(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    # A free model returns valid JSON with a valid id but omits "keep". An
    # unguarded v["keep"] would raise KeyError out of triage() and kill the run.
    # The item must be kept (keep-on-doubt), not crash and not silently dropped.
    respx.post(url__startswith="https://api.groq.com").mock(
        return_value=httpx.Response(200, json=_reply([{"id": "1", "why": "no verdict field"}]))
    )
    verdicts, tier = triage([_item(1, "a")])
    assert tier == "groq"
    assert verdicts[0].keep is True
