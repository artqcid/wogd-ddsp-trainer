#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Character n-gram embeddings and semantic re-ranking.

Pure-standard-library semantic similarity (no sentence-transformers / FAISS).
Used as a secondary re-ranking pass on top of BM25 in the RAG query path.
"""

import math


def char_ngrams(text: str, n_min: int = 2, n_max: int = 4) -> list[str]:
    """Extract character n-grams from a text.

    Uses n-grams of lengths n_min..n_max as feature vectors.
    Pads with '#' at start and end for better boundary detection.
    """
    normalized = text.lower().strip()
    if not normalized:
        return []
    padded = f"#{normalized}#"
    grams = []
    for n in range(n_min, n_max + 1):
        for i in range(len(padded) - n + 1):
            grams.append(padded[i:i + n])
    return grams


def ngram_embedding(text: str) -> dict[str, float]:
    """Generate a TF-weighted n-gram embedding as a dictionary.

    Each n-gram is normalized to its relative frequency (L2-like).
    The result can be used as a sparse embedding for cosine similarity.
    """
    grams = char_ngrams(text)
    if not grams:
        return {}
    freq: dict[str, float] = {}
    for g in grams:
        freq[g] = freq.get(g, 0.0) + 1.0
    # TF normalization
    total = len(grams)
    return {k: v / total for k, v in freq.items()}


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse embeddings."""
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, va in a.items():
        dot += va * b.get(k, 0.0)
    na = sum(v * v for v in a.values())
    nb = sum(v * v for v in b.values())
    denom = math.sqrt(na * nb)
    return dot / denom if denom > 0 else 0.0


def semantic_rerank(query: str, results: list[dict], top_k: int) -> list[dict]:
    """Re-rank results using n-gram cosine similarity.

    Complements BM25 ranking: captures semantic similarity via character
    n-gram overlaps. Does not replace lexical ranking, but mixes it in
    (weighted score).
    """
    if not results or not query.strip():
        return results

    query_emb = ngram_embedding(query)
    if not query_emb:
        return results

    scored = []
    for r in results:
        hay = " ".join([
            r.get("content") or "",
            r.get("symbol_name") or "",
            r.get("signature") or "",
        ])
        doc_emb = ngram_embedding(hay)
        sim = cosine_similarity(query_emb, doc_emb)
        # Combined score: BM25-rank (lower = better) + semantic (higher = better)
        rank = r.get("rank", 0)
        combined = sim * 0.4 + (1.0 / (1.0 + rank)) * 0.6
        scored.append((combined, r))

    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:top_k]]
