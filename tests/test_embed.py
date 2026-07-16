import numpy as np
import pytest

from collect.embed import cosine, dedup, embed, top_against
from collect.models import Item


def _item(title: str, i: int = 0) -> Item:
    return Item(
        source="test", id=str(i), url=f"https://example.com/{i}",
        title=title, body="", created_utc="2026-07-16T00:00:00Z", engagement=0,
    )


@pytest.fixture(scope="module", autouse=True)
def _warm():
    embed(["warm the model cache once"])


def test_embeddings_are_normalized():
    vecs = embed(["a stated problem about renaming files", "something else entirely"])
    assert vecs.shape == (2, 384)
    np.testing.assert_allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-5)


def test_embed_of_nothing_is_empty_not_a_crash():
    assert embed([]).shape == (0, 384)


def test_cosine_ranks_paraphrase_above_unrelated():
    a = embed(["I have to manually rename every exported file"])
    b = embed([
        "Renaming exports by hand every single time is painful",
        "The best sourdough starter needs daily feeding",
    ])
    sims = cosine(a, b)
    assert sims.shape == (1, 2)
    assert sims[0][0] > sims[0][1]


def test_dedup_drops_paraphrases_of_existing_ideas():
    items = [
        _item("I have to manually rename every exported file", 1),
        _item("Kubernetes ingress annotations are undocumented", 2),
    ]
    survivors, dropped = dedup(
        items,
        against=["Renaming exports by hand every time is painful"],
        threshold=0.6,
    )
    assert dropped == 1
    assert len(survivors) == 1
    assert survivors[0].id == "2"


def test_dedup_against_empty_list_keeps_everything():
    # First run: ideas/ is empty. Must not drop the world or divide by zero.
    items = [_item("anything at all", 1)]
    survivors, dropped = dedup(items, against=[], threshold=0.82)
    assert dropped == 0
    assert len(survivors) == 1


def test_top_against_returns_k_sorted_descending():
    items = [
        _item("New Python release improves error messages", 1),
        _item("A recipe for braised short ribs", 2),
        _item("Django 6 ships an async ORM", 3),
    ]
    ranked = top_against(items, reference="I build backend software in Python", k=2)
    assert len(ranked) == 2
    assert ranked[0][1] >= ranked[1][1]
    assert "short ribs" not in ranked[0][0].title
