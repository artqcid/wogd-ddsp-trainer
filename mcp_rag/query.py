#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAG + Code-Wiki search over the SQLite-FTS5 index.

Hybrid search (FTS5/bm25 + exact-identifier boost, optional semantic
re-ranking via character n-grams), plus the symbol-based wiki query and its
LIKE fallbacks. Depends on the `ProjectRAG` storage instance from `db`.
"""

import re
from contextlib import closing

from . import ngrams


def _build_match_expr(query: str) -> str | None:
    """Build a safe FTS5 MATCH expression from the search query.

    The trigram tokenizer requires phrases >= 3 chars. Each term is added
    as a quoted substring joined with AND, so all terms must occur.

    Fallback: if only tokens < 3 chars exist (e.g. "io", "mc"), a
    LIKE-like placeholder '*' is used for FTS5, matching each single
    character as a substring. The query method detects this fallback and
    additionally runs a LIKE search on symbol_name.
    """
    tokens = re.findall(r"[A-Za-z0-9_]{3,}", query)[:20]
    if not tokens:
        return None
    return " AND ".join('"' + t + '"' for t in tokens)


def query_rag(rag, query: str, top_k: int = 3, semantic: bool = False) -> list:
    """Hybrid search: FTS5/bm25 candidates + re-ranking by exact hits.

    Fallback for short queries (< 3 chars): LIKE-based search on
    symbol_name, since the trigram tokenizer does not match short tokens.

    Args:
        rag: ProjectRAG storage instance.
        query: search query.
        top_k: number of results.
        semantic: if True, additional re-ranking via character n-gram
            cosine similarity. Requires no external packages.
    """
    if not query or not query.strip():
        return []
    match_expr = _build_match_expr(query)
    if not match_expr:
        return _query_like_fallback(rag, query, top_k)
    with closing(rag._connect()) as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.chunk_id, c.file_path, c.language, c.line_start, c.line_end,
                   c.content, c.symbol_type, c.symbol_name, c.signature,
                   c.docstring, bm25(code_fts) AS rank
            FROM code_fts
            JOIN code_chunks c ON c.id = code_fts.rowid
            WHERE code_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (match_expr, max(top_k * 4, top_k)),
        ).fetchall()
    rows = [dict(r) for r in rows]

    tokens = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query) if len(t) >= 2]

    def combined(r):
        hay = " ".join([
            r.get("content") or "",
            r.get("symbol_name") or "",
            r.get("signature") or "",
        ])
        exact = sum(
            1 for t in tokens
            if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", hay, re.IGNORECASE)
        )
        return (r["rank"], -exact)

    rows.sort(key=combined)

    if semantic and rows:
        rows = ngrams.semantic_rerank(query, rows, top_k)

    return rows[:top_k]


def _query_like_fallback(rag, query: str, top_k: int = 3) -> list:
    """LIKE fallback for short queries (< 3 chars per token).

    Searches symbol_name, file_path and content via LIKE.
    """
    q = query.strip().lower()
    if not q:
        return []
    like_pattern = "%" + q + "%"
    with closing(rag._connect()) as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.chunk_id, c.file_path, c.language, c.line_start, c.line_end,
                   c.content, c.symbol_type, c.symbol_name, c.signature,
                   c.docstring, 0.0 AS rank
            FROM code_chunks c
            WHERE LOWER(c.symbol_name) LIKE ?
               OR LOWER(c.file_path) LIKE ?
               OR LOWER(c.content) LIKE ?
            ORDER BY c.file_path, c.line_start
            LIMIT ?
            """,
            (like_pattern, like_pattern, like_pattern, top_k),
        ).fetchall()
    return [dict(r) for r in rows]


def query_wiki(rag, query: str, max_results: int = 12) -> list:
    """Symbol-based search in the Code-Wiki (name/signature/docstring)."""
    tokens = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query) if len(t) >= 3]
    if not tokens:
        return _query_wiki_like(rag, query, max_results)
    match_expr = " AND ".join('"' + t + '"' for t in tokens)
    with closing(rag._connect()) as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.chunk_id, c.file_path, c.language, c.line_start,
                   c.line_end, c.symbol_type, c.symbol_name, c.signature,
                   c.docstring
            FROM code_fts
            JOIN code_chunks c ON c.id = code_fts.rowid
            WHERE code_fts MATCH ?
              AND c.symbol_name IS NOT NULL
            ORDER BY bm25(code_fts)
            LIMIT ?
            """,
            (match_expr, max_results),
        ).fetchall()
    return [dict(r) for r in rows]


def _query_wiki_like(rag, query: str, max_results: int = 12) -> list:
    """LIKE fallback for query_wiki on short queries (< 3 chars)."""
    like = "%" + query.strip().lower() + "%"
    with closing(rag._connect()) as conn:
        rows = conn.execute(
            """
            SELECT id, chunk_id, file_path, language, line_start, line_end,
                   symbol_type, symbol_name, signature, docstring
            FROM code_chunks
            WHERE symbol_name IS NOT NULL
              AND (LOWER(symbol_name) LIKE ? OR LOWER(signature) LIKE ?
                   OR LOWER(docstring) LIKE ?)
            ORDER BY file_path, line_start
            LIMIT ?
            """,
            (like, like, like, max_results),
        ).fetchall()
    return [dict(r) for r in rows]
