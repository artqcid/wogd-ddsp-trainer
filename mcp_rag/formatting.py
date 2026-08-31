#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Output serialization of RAG/Wiki search results for LLM consumption.

Pure functions that render hit lists in one of four forms: Markdown "text"
(human-readable), "compact" (one line per hit), "json" (machine-readable) and
"toon" (opt-in, token-sparing TOON encoding). TOON is a pure output filter; it
never touches the RAG database.
"""

import json

try:
    import toon as _toon
except ImportError:  # pragma: no cover - optional serializer
    _toon = None


def chunk_ref(r) -> str:
    """Stable short reference for a chunk: [wogd_ddsp_<hash>]."""
    return f"[{r.get('chunk_id') or r.get('id') or '?'}]"


def _stable_payload(results: list, query: str) -> dict:
    """Build the single stable hit payload shared by json + toon output."""
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "chunk_id": r.get("chunk_id"),
                "file_path": r.get("file_path"),
                "language": r.get("language"),
                "line_start": r.get("line_start"),
                "line_end": r.get("line_end"),
                "symbol_name": r.get("symbol_name"),
                "symbol_type": r.get("symbol_type"),
                "signature": r.get("signature"),
                "content": r.get("content"),
            }
            for r in results
        ],
    }


def format_results(results: list, query: str, format: str = "text") -> str:
    """Format search results for the chat.

    `format` controls the context richness (token optimization):
      - "text":    full Markdown output with code snippets (human-readable)
      - "compact": one line per hit (ID, path, lines, symbol) -
                   full content only via `get_rag_chunk(<id>)`
      - "json":    machine-readable JSON (structured hits incl. IDs)
      - "toon":    TOON-encoded output (opt-in, token-sparing) - same stable
                   structured fields as "json", serialized via `toon.encode`
                   for LLM consumption. Only active when explicitly requested.
    """
    if not results:
        return (
            f"No hits in the RAG database for: '{query}'\n"
            "Tip: run `index_project_code` on the project directory first."
        )
    if format == "toon":
        return format_toon(results, query)
    if format == "json":
        return format_json(results, query)
    if format == "compact":
        return format_compact(results, query)
    lines = [f"RAG search results for: '{query}'", "=" * 60]
    for i, r in enumerate(results, 1):
        lang = r["language"]
        snippet = r["content"]
        if len(snippet) > 900:
            snippet = snippet[:900] + "\n... (truncated)"
        indented = "\n".join("    " + ln for ln in snippet.splitlines())
        lines.append("")
        lines.append(
            f"[{i}] {r['file_path']} (lines {r['line_start']}-{r['line_end']}) "
            f"{chunk_ref(r)}"
        )
        lines.append(f"    Language: {lang}")
        if r.get("symbol_name"):
            lines.append(f"    Symbol: {r['symbol_name']} ({r.get('symbol_type')})")
        if r.get("signature"):
            lines.append(f"    Signature: {r['signature']}")
        lines.append(f"    ```{lang}\n{indented}\n    ```")
    return "\n".join(lines)


def format_compact(results: list, query: str) -> str:
    """Compact output: one line per hit (token-sparing)."""
    if not results:
        return f"No hits in the RAG database for: '{query}'"
    lines = [f"RAG hits (compact) for: '{query}'", "=" * 60]
    for r in results:
        sym = ""
        if r.get("symbol_name"):
            sym = f"{r['symbol_name']} ({r.get('symbol_type')})"
        sig = r.get("signature") or ""
        if sig:
            sig = " :: " + sig.splitlines()[0][:80]
        lines.append(
            f"{chunk_ref(r)} {r['file_path']}:"
            f"{r['line_start']}-{r['line_end']} {sym}{sig}"
        )
    lines.append(
        "Full content of a chunk: call `get_rag_chunk` with its ID."
    )
    return "\n".join(lines)


def format_json(results: list, query: str) -> str:
    """Machine-readable JSON output of the hits (stable fields incl. chunk ID)."""
    return json.dumps(_stable_payload(results, query), ensure_ascii=False, indent=2)


def format_toon(results: list, query: str) -> str:
    """TOON-encoded output of the hits (opt-in, token-sparing for LLMs).

    Reuses the exact same stable payload as `format_json` (identical
    semantics), but serializes it via the optional `toon` dependency
    instead of JSON. TOON is a pure output filter: it does not alter the
    RAG database or any internal storage structure. If `toon` is not
    importable, falls back to the JSON representation.
    """
    payload = _stable_payload(results, query)
    if _toon is not None:
        return _toon.encode(payload)
    return json.dumps(payload, ensure_ascii=False, indent=2)
