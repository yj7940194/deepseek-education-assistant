from __future__ import annotations

"""Simple deterministic text embedding utilities and similarity helpers."""

from typing import Iterable, List, Sequence, Tuple

import numpy as np


EMBEDDING_DIMENSION = 256


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase whitespace-separated tokens."""

    return text.lower().split()


def embed_text(text: str) -> np.ndarray:
    """
    Compute a simple deterministic embedding for the given text.

    The implementation uses a hashed bag-of-words representation mapped into
    a fixed-size vector, which is sufficient for demo RAG purposes.
    """

    vector = np.zeros(EMBEDDING_DIMENSION, dtype=float)
    for token in _tokenize(text):
        index = hash(token) % EMBEDDING_DIMENSION
        vector[index] += 1.0
    norm = np.linalg.norm(vector) or 1.0
    return vector / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two embedding vectors."""

    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def rank_by_similarity(
    query_embedding: np.ndarray,
    candidate_embeddings: Sequence[np.ndarray],
) -> List[Tuple[int, float]]:
    """
    Rank candidate embeddings by cosine similarity to the query embedding.

    Returns a list of (index, score) tuples sorted by descending similarity.
    """

    scores: List[Tuple[int, float]] = []
    for idx, emb in enumerate(candidate_embeddings):
        scores.append((idx, cosine_similarity(query_embedding, emb)))
    scores.sort(key=lambda item: item[1], reverse=True)
    return scores

