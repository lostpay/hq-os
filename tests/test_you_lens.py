from collect.models import Item, RunLog
from collect.you_lens import run_you_lens

PROFILE = """
# profile

## Skills
I ship backend Python and TypeScript. I work with Postgres and deploy on Vercel.

## Domains
Job-application tooling, demand forecasting, personal finance.
"""


def _item(i: int, title: str, source: str = "rss") -> Item:
    return Item(
        source=source, id=str(i), url=f"https://example.com/{i}",
        title=title, body="", created_utc="2026-07-16T00:00:00Z", engagement=0,
    )


def test_ranks_profile_relevant_news_above_irrelevant():
    items = [
        _item(1, "A guide to competitive sourdough baking"),
        _item(2, "Vercel adds native Postgres support for backend deploys"),
        _item(3, "New rules for professional bowling leagues"),
    ]
    log = RunLog(date="2026-07-16", lens="you")
    ranked = run_you_lens(items, PROFILE, log, k=3)

    assert ranked[0][0].id == "2"
    assert ranked[0][1] > ranked[-1][1]


def test_k_caps_the_output():
    items = [_item(i, f"Python release {i}") for i in range(20)]
    log = RunLog(date="2026-07-16", lens="you")
    assert len(run_you_lens(items, PROFILE, log, k=5)) == 5


def test_funnel_is_recorded():
    items = [_item(1, "Postgres news"), _item(2, "bowling")]
    log = RunLog(date="2026-07-16", lens="you")
    run_you_lens(items, PROFILE, log, k=1)

    assert log.counts["raw"] == 2
    assert log.counts["kept"] == 1


def test_empty_profile_raises_rather_than_matching_everything():
    # A vague profile makes a vague lens; an empty one makes no lens at all and
    # would silently return an arbitrary 40 items as if they were relevant.
    import pytest
    with pytest.raises(ValueError, match="profile"):
        run_you_lens([_item(1, "anything")], "   \n\n  ", RunLog(date="d", lens="you"))


def test_no_items_returns_empty_without_crashing():
    log = RunLog(date="2026-07-16", lens="you")
    assert run_you_lens([], PROFILE, log, k=5) == []
    assert log.counts["raw"] == 0
