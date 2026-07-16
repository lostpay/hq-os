"""Embeddings: ~90MB, one forward pass, coordinates out.

Used for the two jobs that are cheap with coordinates and expensive with tokens:
"have I seen this problem before?" (dedup) and "is this about him?" (the you lens).
"""

from __future__ import annotations

import functools
import logging

import numpy as np

from collect.models import Item

log = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIM = 384


@functools.lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    log.info("loading %s", MODEL_NAME)
    return SentenceTransformer(MODEL_NAME)


def embed(texts: list[str]) -> np.ndarray:
    """L2-normalized embeddings, shape (len(texts), 384).

    Normalized so cosine similarity is a plain dot product.
    """
    if not texts:
        return np.zeros((0, DIM), dtype=np.float32)
    return _model().encode(
        texts,
        batch_size=64,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise cosine similarity, shape (len(a), len(b)). Inputs must be normalized."""
    if a.size == 0 or b.size == 0:
        return np.zeros((a.shape[0], b.shape[0]), dtype=np.float32)
    return a @ b.T


def dedup(
    items: list[Item], against: list[str], threshold: float = 0.82
) -> tuple[list[Item], int]:
    """Drop items that paraphrase something already in `against`.

    `against` is every problem statement already in ideas/ plus ideas/archive/. The
    archive is included so a rejected idea does not return every night wearing
    different words.
    """
    if not items or not against:
        return items, 0

    sims = cosine(embed([i.text for i in items]), embed(against))

    keep: list[Item] = []
    dropped = 0
    for item, row in zip(items, sims, strict=True):
        if float(row.max()) >= threshold:
            dropped += 1
        else:
            keep.append(item)

    log.info("dedup: %d in, %d kept, %d dropped", len(items), len(keep), dropped)
    return keep, dropped


def top_against(items: list[Item], reference: str, k: int) -> list[tuple[Item, float]]:
    """The k items most similar to `reference`, most similar first."""
    if not items:
        return []
    sims = cosine(embed([i.text for i in items]), embed([reference]))[:, 0]
    ranked = sorted(
        zip(items, sims, strict=True), key=lambda p: float(p[1]), reverse=True
    )
    return [(item, float(score)) for item, score in ranked[:k]]
