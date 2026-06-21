"""Sentence-Transformers embeddings with a lazy, cached model + hashing fallback."""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("embeddings")


@lru_cache(maxsize=1)
def _model():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.embedding_model)
    except Exception as exc:  # noqa: BLE001
        log.warning("embedding_model_unavailable", error=str(exc))
        return None


def embed(text: str) -> list[float]:
    model = _model()
    if model is not None:
        return model.encode(text, normalize_embeddings=True).tolist()
    return _hash_embed(text)


def embed_many(texts: list[str]) -> list[list[float]]:
    model = _model()
    if model is not None:
        return [v.tolist() for v in model.encode(texts, normalize_embeddings=True)]
    return [_hash_embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _hash_embed(text: str, dim: int = 384) -> list[float]:
    """Deterministic bag-of-hashed-tokens vector — keeps similarity usable offline."""
    vec = [0.0] * dim
    for tok in text.lower().split():
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
