#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP server for the wogd-ddsp-trainer project.

Provides a lightweight RAG (Retrieval-Augmented Generation) + Code-Wiki
toolchain for coding agents, built with the Python standard library
(ast, sqlite3, re) and FastMCP. The implementation lives in the `mcp_rag`
package (chunking, db, query, formatting, wiki) so each concern stays small
and navigable; this file is a thin entry point that (a) owns the project
paths, (b) instantiates the shared RAG database and (c) registers the MCP
tools. The optional `toon` dependency is only used as an output serializer
(format="toon") for token-optimized LLM consumption; it never touches the
RAG database or internal storage structures.

Web front-end languages (TS/JS/Vue/HTML/CSS/JSON) are indexed via a generic
line-chunker so their content stays full-text searchable.
"""

from fastmcp import FastMCP
import os
import sys
import sqlite3
from contextlib import closing

from mcp_rag import ProjectRAG, formatting, query as ragquery
from mcp_rag import wiki as ragwiki


# Ensure UTF-8 stdio on Windows (defensive against cp1252 consoles).
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

# Initialize the FastMCP server
mcp = FastMCP("WOGD_DDSP-Assistant")


# ============================================================================
# RAG-LLM-Wiki (Retrieval-Augmented Generation + Code-Wiki)
# ----------------------------------------------------------------------------
# Lightweight combination of three concepts, using only Python's standard
# library (ast, sqlite3, re) - no new packages needed:
#
#   1. Structural code chunking (repo-level RAG / AST instead of line chunks):
#      - Python: stdlib `ast` -> classes/functions/methods with qualified
#        names, signatures and docstrings; imports stay in the module chunk.
#      - C++: brace-based scanner (no tree-sitter) -> functions, classes
#        (incl. methods), namespaces/extern "C"; #includes stay in the module
#        chunk.
#      - Markdown: chunking by headings (sections).
#      Each chunk carries metadata (symbol_type, symbol_name, signature,
#      docstring) -> class/method context is preserved and the symbol index
#      feeds the Code-Wiki.
#
#   2. Hybrid search: SQLite FTS5 with trigram tokenizer (bm25, lexical -
#      also finds identifier substrings) plus re-ranking by exact identifier
#      hits (syntax/hybrid boost). No vector DB needed.
#
#   3. Code-Wiki (doc/code_wiki.md): stable, committed symbol index
#      (file -> symbols with signature/docstring/lines). Agents read the wiki
#      once per session (stable context = prompt-cache friendly) and use
#      query_code_rag / query_code_wiki for targeted code locations.
# ============================================================================

# Database file lives next to this script in the project directory
RAG_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wogd_ddsp.db")

# Path to the generated Code-Wiki (stable symbol index, committed)
WIKI_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "doc", "code_wiki.md"
)


# RAG instance is kept global so all tools use the same database.
_rag = ProjectRAG(RAG_DB_PATH)


# ============================================================================
# SQLite-RAG Tools
# ============================================================================


@mcp.tool()
def index_project_code(directory_path: str) -> str:
    """Index the project directory into the SQLite RAG database (wogd_ddsp.db).

    Recursively scans for C++ files (.cpp/.h/.hpp/.cc/.cxx/.c), Python files
    (.py) and Markdown docs (.md, incl. AGENTS.md)
    and splits them **structurally** instead of into fixed line blocks: Python
    via `ast` (classes/functions/methods), C++ via a brace-based scanner
    (functions/classes/methods/namespaces), Markdown by headings. Each chunk
    carries symbol metadata (type, name, signature, docstring).

    Afterwards the Code-Wiki `doc/code_wiki.md` is regenerated (stable symbol
    index with file paths and line numbers - read once per session by coding
    agents). Unchanged files are detected by SHA-256 hash and skipped
    (incremental re-indexing).

    Args:
        directory_path: absolute path to the project directory (e.g. the
            workspace root `wogd-ddsp-trainer`).

    Returns:
        Summary of the indexing run including wiki status.
    """
    try:
        stats = _rag.index_directory(directory_path)
    except ValueError as e:
        return f"Error: {e}"
    except sqlite3.Error as e:
        return f"Database error: {e}"

    wiki_line = ""
    try:
        wiki = ragwiki.generate_wiki(_rag, WIKI_PATH)
        wiki_line = (
            f"\n  - Code-Wiki regenerated: {wiki['path']}\n"
            f"    ({wiki['symbols']} symbols in {wiki['files']} files)"
        )
    except OSError as e:
        wiki_line = f"\n  - Wiki generation skipped: {e}"

    return (
        f"Indexing complete:\n"
        f"  - Files scanned: {stats['total_files']}\n"
        f"  - Newly indexed: {stats['indexed']}\n"
        f"  - Unchanged skipped: {stats['skipped']}\n"
        f"  - Database: {_rag.db_path}"
        f"{wiki_line}\n\n"
        "Wiki updated. Agents: re-read doc/code_wiki.md. Use `query_code_rag` for targeted code locations and "
        "`query_code_wiki` for the symbol/structure search."
    )


@mcp.tool()
def query_code_rag(query: str, top_k: int = 3, format: str = "text", semantic: bool = False) -> str:
    """Search the RAG database for code locations matching the query.

    Hybrid search: SQLite FTS5 with trigram tokenizer (bm25, lexical - also
    matches identifier substrings such as `block_size`, `dsp_setup`) plus
    re-ranking by exact identifier hits (syntax boost). Hits carry stable
    chunk references ([wogd_ddsp_<hash>]) usable for `get_rag_chunk`.

    Args:
        query: search query, e.g. "shared memory handshake" or "enable handler".
        top_k: number of results to return (default: 3).
        format: output format - "text" (code snippets, default), "compact"
            (one line per hit, token-sparing), "json" (machine-readable,
            incl. chunk_id) or "toon" (TOON-encoded, opt-in, token-sparing
            for LLM consumption - same structured fields as "json").
        semantic: if True, additional semantic re-ranking via character
            n-gram cosine similarity. Requires no external packages.

    Returns:
        The most relevant code chunks incl. file path, line numbers and chunk ID.
    """
    if not _rag_has_data():
        return (
            "The RAG database is empty.\n"
            "Run `index_project_code` on the project directory first."
        )
    results = ragquery.query_rag(_rag, query, top_k=top_k, semantic=semantic)
    return formatting.format_results(results, query, format=format)


@mcp.tool()
def get_rag_chunk(chunk_id: str) -> str:
    """Return the full content of a single RAG chunk (transient).

    Complement to `query_code_rag`/`query_code_wiki`: in compact/toon mode
    these tools return only short references ([wogd_ddsp_<id>]). This function
    returns the full code/text of a chunk - only when it is actually needed in
    detail during reasoning (avoids unnecessary context dumping).

    Args:
        chunk_id: chunk reference in the format "wogd_ddsp_<id>" (from search results).

    Returns:
        Full chunk content with metadata.
    """
    if not chunk_id or not chunk_id.startswith("wogd_ddsp_"):
        return (
            f"Invalid chunk ID: '{chunk_id}'. Expected the format "
            "'wogd_ddsp_<hash>' from `query_code_rag`/`query_code_wiki`."
        )
    with closing(_rag._connect()) as conn:
        row = conn.execute(
            """
            SELECT id, chunk_id, file_path, language, line_start, line_end, content,
                   symbol_type, symbol_name, signature, docstring
            FROM code_chunks WHERE chunk_id = ?
            """,
            (chunk_id,),
        ).fetchone()
    if not row:
        return f"No chunk with ID '{chunk_id}' in the RAG database."
    r = dict(row)
    header = (
        f"Chunk {formatting.chunk_ref(r)}: {r['file_path']} "
        f"(lines {r['line_start']}-{r['line_end']})"
    )
    if r.get("symbol_name"):
        header += f"\n  Symbol: {r['symbol_name']} ({r.get('symbol_type')})"
    if r.get("signature"):
        header += f"\n  Signature: {r['signature']}"
    body = r["content"]
    if len(body) > 8000:
        body = body[:8000] + "\n... (chunk truncated to 8000 chars)"
    return header + "\n```" + (r["language"] or "") + "\n" + body + "\n```"


@mcp.tool()
def query_code_wiki(query: str, max_results: int = 12, format: str = "text") -> str:
    """Search the Code-Wiki symbol index for classes, functions and methods.

    Searches over symbol_name, signature and docstring of the structured
    chunks (not the full text of the implementation). Returns the found
    symbols with type, file path and line numbers - ideal as a starting point
    for structure/architecture questions ("which method does X?", "where is Y
    defined?"). For implementation details afterwards use `query_code_rag`.

    Args:
        query: search term, e.g. "apply_io", "SharedMemoryManager" or "handshake".
        max_results: max number of symbols (default: 12).
        format: output format - "text" (default), "compact" (one line per
            symbol), "json" (machine-readable, incl. chunk_id) or "toon"
            (TOON-encoded, opt-in, token-sparing for LLM consumption).

    Returns:
        Found symbols with file path, line numbers, signature and docstring.
    """
    if not _rag_has_data():
        return (
            "The RAG database is empty.\n"
            "Run `index_project_code` on the project directory first."
        )
    rows = ragquery.query_wiki(_rag, query, max_results)
    if not rows:
        return (
            f"No wiki symbols for: '{query}'\n"
            "Tip: `query_code_wiki` searches symbol names/signatures. For "
            "full text in implementation code use `query_code_rag`."
        )
    if format != "text":
        return formatting.format_results(rows, query, format=format)
    lines = [f"Code-Wiki symbols for: '{query}'", "=" * 60]
    for i, r in enumerate(rows, 1):
        sig = r.get("signature") or ""
        doc_lines = (r.get("docstring") or "").strip().splitlines()
        doc1 = doc_lines[0][:160] if doc_lines else ""
        lines.append("")
        lines.append(f"[{i}] {r['symbol_name']} ({r['symbol_type']})")
        lines.append(f"    {r['file_path']}:{r['line_start']}-{r['line_end']}")
        if sig:
            lines.append(f"    {sig}")
        if doc1:
            lines.append(f"    {doc1}")
    return "\n".join(lines)


def _rag_has_data() -> bool:
    """Check whether the RAG database already contains code chunks."""
    try:
        with closing(_rag._connect()) as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM code_chunks").fetchone()
        return bool(row and row["n"] > 0)
    except sqlite3.Error:
        return False


if __name__ == "__main__":
    mcp.run()
