from collect.fetch import fetch_safely
from collect.models import Item


def _item(i: int = 1) -> Item:
    return Item(
        source="test",
        id=str(i),
        url=f"https://example.com/{i}",
        title="I have to manually rename every export",
        body="Every time I export a report I rename it by hand.",
        created_utc="2026-07-16T00:00:00Z",
        engagement=3,
    )


def test_successful_fetch_returns_items():
    result = fetch_safely("test", lambda: [_item()])
    assert result.name == "test"
    assert len(result.items) == 1
    assert result.error is None
    assert result.zero_yield is False


def test_raising_source_is_isolated_not_propagated():
    def boom() -> list[Item]:
        raise RuntimeError("API returned 500")

    result = fetch_safely("broken", boom)
    assert result.items == []
    assert result.error is not None
    assert "RuntimeError" in result.error
    assert "API returned 500" in result.error


def test_empty_result_is_flagged_as_zero_yield():
    # A source returning nothing without raising is the dangerous case: it lets a
    # routine conclude "no problems today" from a silent breakage.
    result = fetch_safely("quiet", lambda: [])
    assert result.items == []
    assert result.error is None
    assert result.zero_yield is True


def test_item_text_concatenates_title_and_body_for_embedding():
    assert _item().text == (
        "I have to manually rename every export\n\n"
        "Every time I export a report I rename it by hand."
    )
