#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP server for the wogd-ddsp-trainer project.

Provides a lightweight RAG (Retrieval-Augmented Generation) + Code-Wiki
toolchain for coding agents, built exclusively with the Python standard
library (ast, sqlite3, re) and FastMCP. No extra data-science packages needed.

Adapted from the netsdr_rag MCP server of the wogd-vst-netsdrstation project
(netsdr_mcp_server.py). The original file is read-only; this is an independent,
project-specific adaptation in English for a Python + Web-UI DDSP training
project. Web front-end languages (TS/JS/Vue/HTML/CSS/JSON) are indexed via a
generic line-chunker so their content stays full-text searchable.
"""

from fastmcp import FastMCP
import subprocess
import os
import sys
import re
import ast
import json
import hashlib
import sqlite3
from contextlib import closing
import fnmatch
import math

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

# Schema version: bump on structural changes -> forces a DB rebuild.
# v1 = line chunking, v2 = structural chunking + symbol metadata.
# v3 = C++ header reconstruction (multi-line signatures) + LF normalization.
# v4 = Stable chunk IDs (hash-based instead of AUTOINCREMENT).
# v5 = Recreate FTS5 when upgrading databases created with the incomplete
#      symbol-index schema.
# v6 = YAML frontmatter column for Markdown concept files (LLM-Wiki/OKF).
# v7 = wogd-ddsp-trainer adaptation: wogd_ddsp_ chunk ID prefix, web front-end
#      languages (TS/JS/Vue/HTML/CSS/JSON) via generic line-chunker.
RAG_SCHEMA_VERSION = 7

# Languages to index and their file extensions.
# `.md` is included so that the central guide
# (AGENTS.md, docs) is searchable via RAG.
# Python = torch/trainer code (structural AST chunking), cpp = extension/DSP
# modules, markdown = LLM-Wiki concept files (heading chunking), everything
# else (web UI) falls through to generic line chunking.
RAG_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".md": "markdown",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".vue": "javascript",
    ".html": "markup",
    ".css": "markup",
    ".json": "json",
    ".toml": "json",
    ".yaml": "json",
    ".yml": "json",
}

# Max length of a module chunk (code outside named symbols) in lines.
MODULE_CHUNK_LINES = 60

# Directories skipped during scanning. SDK/framework dirs/flood the
# index with foreign code and dilute searches in the project's own code.
RAG_IGNORED_DIRS = {
    ".git", "build", "dist", "out", ".venv", "__pycache__", ".pytest_cache",
    "node_modules", ".continue", "CMakeFiles", ".vscode", ".idea",
    "third_party",
}

# Max file size to index (bytes) - prevents large binaries
RAG_MAX_FILE_SIZE = 2 * 1024 * 1024

# Do not index the generated wiki itself (meta-noise, new hash each run)
RAG_IGNORED_FILENAMES = {"code_wiki.md"}


# ---------------------------------------------------------------------------
# Structural chunking (AST / brace-based / headings)
# ---------------------------------------------------------------------------

def _stable_chunk_id(file_path: str, line_start: int, symbol_name: str | None,
                     line_end: int | None = None) -> str:
    """Generate a stable chunk ID from file path, start/end line and symbol name.

    Hash-based (SHA-256, first 12 hex chars = 48 bits), so the ID stays stable
    across sessions and re-indexes (unlike AUTOINCREMENT). The format matches
    `[wogd_ddsp_<hash>]` and is compatible with get_rag_chunk.

    `line_end` is included so that two chunks which share a start line and
    symbol name (e.g. overlapping member-declaration blocks emitted by the brace
    scanner) still get distinct IDs — otherwise the UNIQUE(chunk_id) constraint
    aborts incremental indexing.
    """
    raw = f"{file_path}::{line_start}::{line_end}::{symbol_name or ''}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"wogd_ddsp_{h}"


# ---------------------------------------------------------------------------
# Character N-Gram Embeddings (semantic similarity without external
# dependencies like sentence-transformers or FAISS)
# ---------------------------------------------------------------------------

def _char_ngrams(text: str, n_min: int = 2, n_max: int = 4) -> list[str]:
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


def _ngram_embedding(text: str) -> dict[str, float]:
    """Generate a TF-weighted n-gram embedding as a dictionary.

    Each n-gram is normalized to its relative frequency (L2-like).
    The result can be used as a sparse embedding for cosine similarity.
    """
    grams = _char_ngrams(text)
    if not grams:
        return {}
    freq: dict[str, float] = {}
    for g in grams:
        freq[g] = freq.get(g, 0.0) + 1.0
    # TF normalization
    total = len(grams)
    return {k: v / total for k, v in freq.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
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


def _semantic_rerank(query: str, results: list[dict], top_k: int) -> list[dict]:
    """Re-rank results using n-gram cosine similarity.

    Complements BM25 ranking: captures semantic similarity via character
    n-gram overlaps. Does not replace lexical ranking, but mixes it in
    (weighted score).
    """
    if not results or not query.strip():
        return results

    query_emb = _ngram_embedding(query)
    if not query_emb:
        return results

    scored = []
    for r in results:
        hay = " ".join([
            r.get("content") or "",
            r.get("symbol_name") or "",
            r.get("signature") or "",
        ])
        doc_emb = _ngram_embedding(hay)
        sim = _cosine_similarity(query_emb, doc_emb)
        # Combined score: BM25-rank (lower = better) + semantic (higher = better)
        rank = r.get("rank", 0)
        combined = sim * 0.4 + (1.0 / (1.0 + rank)) * 0.6
        scored.append((combined, r))

    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:top_k]]


def _emit_chunk(lines, start, end, symbol_type, symbol_name, signature, docstring, file_path="") -> dict:
    """Build a chunk record from a 0-based line range [start, end].

    Contains a stable chunk ID (hash-based) that stays valid across
    sessions and re-indexes.
    """
    line_start = start + 1
    return {
        "line_start": line_start,
        "line_end": end + 1,
        "content": "\n".join(lines[start:end + 1]),
        "symbol_type": symbol_type,
        "symbol_name": symbol_name,
        "signature": (signature or "").strip() or None,
        "docstring": docstring,
        "chunk_id": _stable_chunk_id(file_path, line_start, symbol_name, end + 1),
    }


def _module_chunks(lines, start, end, file_path="") -> list:
    """Split a region without named symbols into max 60-line blocks."""
    start = max(0, start)
    end = min(len(lines) - 1, end)
    if start > end:
        return []
    out = []
    for s in range(start, end + 1, MODULE_CHUNK_LINES):
        e = min(end, s + MODULE_CHUNK_LINES - 1)
        out.append(_emit_chunk(lines, s, e, "module", None, None, None, file_path))
    return out


def _py_arglist(args) -> str:
    """Build a compact parameter list (with defaults) from ast.arguments."""
    parts = []
    npos = len(args.args)
    ndef = len(args.defaults)
    for i, a in enumerate(args.args):
        s = a.arg
        d = i - (npos - ndef)
        if d >= 0 and d < ndef and args.defaults[d] is not None:
            try:
                s += "=" + ast.unparse(args.defaults[d])
            except Exception:
                pass
        parts.append(s)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    parts.extend(a.arg for a in args.kwonlyargs)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    return "(" + ", ".join(parts) + ")"


def _py_bases(node) -> str:
    if not node.bases:
        return ""
    names = []
    for b in node.bases:
        try:
            names.append(ast.unparse(b))
        except Exception:
            names.append("...")
    return "(" + ", ".join(names) + ")"


def _chunk_python(source: str, file_path: str = "") -> list:
    """Split Python code via stdlib `ast` into classes/functions/methods.

    Returns chunks with symbol_type (class/function/method), qualified name,
    signature and docstring. Lines outside definitions (imports, constants)
    are collected as `module` chunks.
    """
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = source.split("\n")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _module_chunks(lines, 0, len(lines) - 1, file_path)

    chunks = []
    covered = []  # 1-based intervals [lineno, end_lineno] of the definitions

    # Top-level uppercase assignments are module constants, not anonymous
    # module text. Keep them as named symbols so the wiki can index protocol
    # constants such as MAGIC_NUMBER.
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                chunks.append(_emit_chunk(
                    lines, node.lineno - 1, node.end_lineno - 1,
                    "constant", target.id, lines[node.lineno - 1].strip(),
                    None, file_path))
                covered.append((node.lineno, node.end_lineno))

    def walk(body, parent):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{parent}.{node.name}" if parent else node.name
                kind = "method" if parent else "function"
                sig = "def " + node.name + _py_arglist(node.args)
                doc = ast.get_docstring(node)
                chunks.append(_emit_chunk(
                    lines, node.lineno - 1, node.end_lineno - 1,
                    kind, name, sig, doc, file_path))
                covered.append((node.lineno, node.end_lineno))
            elif isinstance(node, ast.ClassDef):
                name = f"{parent}.{node.name}" if parent else node.name
                sig = "class " + node.name + _py_bases(node)
                doc = ast.get_docstring(node)
                chunks.append(_emit_chunk(
                    lines, node.lineno - 1, node.end_lineno - 1,
                    "class", name, sig, doc, file_path))
                covered.append((node.lineno, node.end_lineno))
                walk(node.body, name)

    walk(tree.body, None)

    if not covered:
        return _module_chunks(lines, 0, len(lines) - 1, file_path)

    cursor = 1
    for a, b in sorted(covered):
        if a > cursor:
            chunks.extend(_module_chunks(lines, cursor - 1, a - 2, file_path))
        cursor = max(cursor, b + 1)
    if cursor <= len(lines):
        chunks.extend(_module_chunks(lines, cursor - 1, len(lines) - 1, file_path))

    chunks.sort(key=lambda c: c["line_start"])
    return chunks


# Control keywords that are not a function head (C++ heuristic)
_CPP_CTRL = {"if", "for", "while", "switch", "catch", "do", "else", "return",
             "sizeof", "new", "delete"}


def _cpp_def_kind(header: str):
    """Classify a C++ block head -> (kind, name).

    kinds: namespace, extern, class, function, block.
    """
    h = header.strip()
    if not h or h.startswith("#") or h.endswith(";"):
        return ("block", None)
    m = re.match(r"namespace\s+([A-Za-z_]\w*)", h)
    if m:
        return ("namespace", m.group(1))
    # Check for extern "C" + function before the generic extern block check.
    m = re.match(r'extern\s*"C"\s+.*?([A-Za-z_]\w*)\s*\(', h)
    if m and m.group(1) not in _CPP_CTRL:
        return ("function", m.group(1))
    if re.match(r'extern\s*"C"', h):
        return ("extern", None)
    m = re.match(
        r"(?:template\s*<[^>]*>\s*)?"
        r"(?:(?:typedef\s+)?(?:class|struct|union)\s+([A-Za-z_]\w*)|"
        r"enum(?:\s+class)?\s+([A-Za-z_]\w*))",
        h,
    )
    if m:
        return ("class", m.group(1) or m.group(2))
    m = re.search(r"([A-Za-z_]\w*)\s*\(", h)
    if m and m.group(1) not in _CPP_CTRL:
        return ("function", m.group(1))
    return ("block", None)


def _cpp_collect_header(lines, idx, prefix):
    """Reconstruct the full block head (multi-line signatures).

    If the `{` sits in the middle of a multi-line signature (e.g.
    ``inline bool foo(int a,\n                 long b) {``) or on its own line
    (``long b)\n{``), the scanner runs backwards over continuation lines and
    collects the whole head. Stops at boundaries: blank line, comment,
    preprocessor `#`, or a line ending with `;`/`{`/`}`.

    Returns:
        (header, start_idx): head text and index of its first line.
    """
    header = prefix.strip()
    start = idx
    j = idx - 1
    while j >= 0:
        stripped = lines[j].strip()
        if not stripped or stripped.startswith(("//", "*", "/*", "*/", "#")):
            break
        prev = lines[j].lstrip().rstrip()
        if prev and prev[-1] in "{};":
            break
        header = stripped + " " + header
        start = j
        j -= 1
    return header, start


def _cpp_sub_blocks(lines, start, end, base) -> list:
    """Find blocks at depth base+1 in the range [start, end].

    Returns (header_idx, header_line, end_idx). The header is reconstructed
    from the line before the `{` (supports multi-line signatures). One-line
    blocks (e.g. `int a[] = {1,2};`) are ignored (noise).
    """
    blocks = []
    depth = base
    pending = None
    for idx in range(start, end + 1):
        line = lines[idx]
        if pending is None and depth == base and "{" in line:
            brace = line.index("{")
            prefix = line[:brace].strip()
            if prefix:
                header, hstart = _cpp_collect_header(lines, idx, prefix)
                pending = (hstart, header)
            else:
                j = idx - 1
                while j >= start and not lines[j].strip():
                    j -= 1
                if j >= start:
                    header, hstart = _cpp_collect_header(lines, idx, lines[j].strip())
                    pending = (hstart, header)
                else:
                    pending = (idx, prefix)
        depth += line.count("{") - line.count("}")
        if pending is not None and depth == base:
            if pending[0] < idx:  # real blocks, not one-liners
                blocks.append((pending[0], pending[1], idx))
            pending = None
    return blocks


def _chunk_cpp_class(lines, start, end, base, name, file_path="") -> list:
    """Split a C++ class: methods separately, header/members as class chunk."""
    blocks = _cpp_sub_blocks(lines, start + 1, end - 1, base + 1)
    if not blocks:
        chunks = [_emit_chunk(lines, start, end, "class", name,
                              lines[start].strip(), None, file_path)]
        # A typedef struct has two useful names: the tag (e.g. _mab_info)
        # and the public typedef alias (e.g. t_mab_info). Keep the tag as the
        # primary class symbol, but index the alias too for callers using the
        # public C type name.
        alias_match = re.search(r"}\s*([A-Za-z_]\w*)\s*;", lines[end].strip())
        if alias_match and alias_match.group(1) != name:
            chunks.append(_emit_chunk(
                lines, start, end, "class", alias_match.group(1),
                lines[start].strip(), None, file_path))
        return chunks

    chunks = []
    cursor = start
    for (hdr_idx, hdr_line, end_idx) in blocks:
        if hdr_idx > cursor:
            chunks.append(_emit_chunk(lines, cursor, hdr_idx - 1, "class", name,
                                      lines[start].strip(), None, file_path))
        kind, mname = _cpp_def_kind(hdr_line)
        if kind == "function" and mname:
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "method",
                                      f"{name}::{mname}", hdr_line, None, file_path))
        else:
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "block", name,
                                      hdr_line, None, file_path))
        cursor = end_idx + 1
    if cursor <= end:
        chunks.append(_emit_chunk(lines, cursor, end, "class", name,
                                  lines[start].strip(), None, file_path))
    return chunks


def _chunk_cpp_defines(lines, file_path="") -> list:
    """Extract #define constants as named chunks."""
    chunks = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        m = re.match(r'#define\s+([A-Za-z_]\w*)\s+(.+)', stripped)
        if m:
            chunks.append(_emit_chunk(
                lines, idx, idx, "constant", m.group(1), stripped, None,
                file_path))
    return chunks


def _chunk_cpp_region(lines, start, end, base, file_path="") -> list:
    """Split a C++ region: blocks at depth base+1 + module gaps."""
    chunks = []
    blocks = _cpp_sub_blocks(lines, start, end, base)
    cursor = start
    for (hdr_idx, hdr_line, end_idx) in blocks:
        if hdr_idx > cursor:
            chunks.extend(_module_chunks(lines, cursor, hdr_idx - 1, file_path))
        kind, name = _cpp_def_kind(hdr_line)
        if kind in ("namespace", "extern"):
            inner = _chunk_cpp_region(lines, hdr_idx + 1, end_idx - 1, base + 1, file_path)
            if inner:
                chunks.extend(inner)
            else:
                chunks.append(_emit_chunk(lines, hdr_idx, end_idx, kind, name,
                                          hdr_line, None, file_path))
        elif kind == "class":
            chunks.extend(_chunk_cpp_class(lines, hdr_idx, end_idx, base, name, file_path))
        elif kind == "function":
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "function", name,
                                      hdr_line, None, file_path))
        else:
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "block", name,
                                      hdr_line, None, file_path))
        cursor = end_idx + 1
    if cursor <= end:
        chunks.extend(_module_chunks(lines, cursor, end, file_path))
    return chunks


def _chunk_cpp(source: str, file_path: str = "") -> list:
    """Split C++ code structurally (brace-based, without tree-sitter)."""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = source.split("\n")
    chunks = _chunk_cpp_defines(lines, file_path)
    chunks.extend(_chunk_cpp_region(lines, 0, len(lines) - 1, 0, file_path))
    return chunks


def _parse_frontmatter(lines: list[str]) -> tuple[dict | None, int]:
    """Extract OKF YAML frontmatter from the top of a Markdown file.

    Returns (frontmatter_dict, body_start_index).
    frontmatter_dict is None when no ``---``-delimited block is found.
    Parsing is simple line-based: supports unquoted scalars, nested
    mappings (indented), and inline lists. No external YAML dependency.
    """
    if not lines or not lines[0].strip().startswith("---"):
        return None, 0
    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end < 0:
        return None, 0
    fm: dict = {}
    current_key: str | None = None
    current_map: dict | None = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            key_part = stripped.split(":", 1)[0].rstrip()
            val_part = stripped.split(":", 1)[1].strip()
            # Top-level key:value
            if not raw.startswith(" ") and not raw.startswith("\t"):
                current_key = key_part
                current_map = fm
                if val_part:
                    # Inline list? [a, b, c]
                    if val_part.startswith("[") and val_part.endswith("]"):
                        fm[current_key] = [
                            v.strip().strip("'\"")
                            for v in val_part[1:-1].split(",") if v.strip()
                        ]
                    elif val_part.startswith('"') and val_part.endswith('"'):
                        fm[current_key] = val_part[1:-1]
                    else:
                        fm[current_key] = val_part
                else:
                    # Nested mapping starts
                    fm[current_key] = {}
                    current_map = fm[current_key]
            else:
                # Nested key under current mapping
                if current_map is not None and isinstance(current_map, dict):
                    if val_part:
                        if val_part.startswith('"') and val_part.endswith('"'):
                            current_map[key_part] = val_part[1:-1]
                        else:
                            current_map[key_part] = val_part
        # Empty nested value (e.g. `verified:` with no inline value)
        elif raw.startswith(" ") and current_map is not None and isinstance(current_map, dict) and ":" in stripped.rstrip(":"):
            pass  # mapping key will get its sub-keys later
    return fm if fm else None, end + 1


def _chunk_markdown(source: str, file_path: str = "") -> list:
    """Split Markdown by headings (sections = chunks).

    YAML frontmatter (``---`` ... ``---`` at the top of the file) is extracted
    and stored as a dedicated ``frontmatter`` chunk so the code wiki can carry
    concept metadata (OKF type, status, description, stale_after, etc.).
    """
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = source.split("\n")
    fm, body_start = _parse_frontmatter(lines)
    chunks = []
    # Frontmatter as a named chunk for wiki metadata
    if fm:
        chunks.append(_emit_chunk(
            lines, 0, body_start - 1, "frontmatter",
            fm.get("title") or os.path.basename(file_path),
            None, fm.get("description") or "", file_path))
    headings = [i for i, ln in enumerate(lines) if re.match(r"^#{1,6}\s", ln) and i >= body_start]
    if not headings:
        chunks.extend(_module_chunks(lines, body_start, len(lines) - 1, file_path))
        return chunks
    if headings[0] > body_start:
        chunks.extend(_module_chunks(lines, body_start, headings[0] - 1, file_path))
    for k, hi in enumerate(headings):
        e = headings[k + 1] - 1 if k + 1 < len(headings) else len(lines) - 1
        title = re.sub(r"^#+\s*", "", lines[hi]).strip() or lines[hi].strip()
        chunks.append(_emit_chunk(lines, hi, e, "section", title,
                                  lines[hi].strip(), None, file_path))
    return chunks


class ProjectRAG:
    """Manages the local SQLite-FTS5 database for code retrieval."""

    def __init__(self, db_path: str = RAG_DB_PATH):
        self.db_path = db_path
        self._init_schema()

    # -- Database connection ------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        """Open a fresh connection (thread-safe for parallel MCP calls)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    # -- Schema --------------------------------------------------------------
    def _init_schema(self):
        """Create the tables; migrate old schemas (line chunking -> v2)."""
        with closing(self._connect()) as conn:
            with conn:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version < RAG_SCHEMA_VERSION:
                    conn.execute("DROP TABLE IF EXISTS code_fts")
                    conn.execute("DROP TABLE IF EXISTS code_chunks")
                    conn.execute("PRAGMA user_version = {}".format(RAG_SCHEMA_VERSION))
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS code_chunks (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        chunk_id    TEXT    NOT NULL UNIQUE,
                        file_path   TEXT    NOT NULL,
                        language    TEXT    NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        line_start  INTEGER NOT NULL,
                        line_end    INTEGER NOT NULL,
                        content     TEXT    NOT NULL,
                        symbol_type TEXT,
                        symbol_name TEXT,
                        signature   TEXT,
                        docstring   TEXT,
                        frontmatter TEXT,
                        file_sha    TEXT    NOT NULL,
                        UNIQUE(file_path, chunk_index)
                    )
                """)
                # FTS5 virtual table: rowid references code_chunks.id.
                # Trigram tokenizer preferred, fallback to unicode61.
                # v4: symbol_name, signature, docstring as searchable FTS5 fields.
                fts_sql = (
                    "CREATE VIRTUAL TABLE IF NOT EXISTS code_fts USING fts5("
                    "file_path UNINDEXED, language UNINDEXED, "
                    "line_start UNINDEXED, line_end UNINDEXED, "
                    "symbol_name, signature, docstring, content, "
                    "tokenize = '{}')"
                )
                try:
                    conn.execute(fts_sql.format("trigram"))
                except sqlite3.OperationalError:
                    # Older SQLite builds without the trigram tokenizer
                    conn.execute(fts_sql.format("unicode61"))
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_code_chunks_path "
                    "ON code_chunks(file_path)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_code_chunks_symbol "
                    "ON code_chunks(symbol_name)"
                )

    # -- Scanning ------------------------------------------------------------
    def _scan_directory(self, directory_path: str) -> list:
        """Collect all indexable source files under directory_path."""
        # .ragignore load (optional)
        ragignore_patterns = []
        ragignore_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".ragignore"
        )
        if os.path.isfile(ragignore_path):
            with open(ragignore_path, "r", encoding="utf-8") as rf:
                for raw in rf:
                    line = raw.strip()
                    if line and not line.startswith("#"):
                        ragignore_patterns.append(line)

        def _is_ignored(abs_path: str, rel_path: str) -> bool:
            for pat in ragignore_patterns:
                if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(abs_path, pat):
                    return True
                # Also match a directory prefix (e.g. "build/" matches "build/Debug/file.cpp")
                if pat.endswith("/") and (rel_path.startswith(pat) or abs_path.startswith(pat)):
                    return True
            return False

        files = []
        for root, dirs, names in os.walk(directory_path):
            dirs[:] = [d for d in dirs if d not in RAG_IGNORED_DIRS]
            for name in names:
                if name in RAG_IGNORED_FILENAMES:
                    continue
                ext = os.path.splitext(name)[1].lower()
                lang = RAG_LANGUAGE_EXTENSIONS.get(ext)
                if not lang:
                    continue
                abs_path = os.path.join(root, name)
                try:
                    rel_path = os.path.relpath(abs_path, directory_path)
                except ValueError:
                    rel_path = abs_path
                if _is_ignored(abs_path, rel_path):
                    continue
                try:
                    if os.path.getsize(abs_path) > RAG_MAX_FILE_SIZE:
                        continue
                    with open(abs_path, "rb") as f:
                        content_bytes = f.read()
                except OSError:
                    continue
                try:
                    content = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content = content_bytes.decode("utf-8", errors="replace")
                content = content.replace("\r\n", "\n").replace("\r", "\n")
                files.append({
                    "path": os.path.normpath(abs_path),
                    "language": lang,
                    "sha": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "content": content,
                })
        return files

    def _chunk_file(self, language: str, content: str, file_path: str = "") -> list:
        """Chunk a source file language-dependently (structural instead of line blocks).

        Python/C++ are structurally chunked (AST / brace scanner); Markdown by
        headings. All other languages (web front-end: TS/JS/Vue/HTML/CSS/JSON,
        config files) fall through to generic line chunking so their full text
        stays searchable via RAG/FTS5.
        """
        if language == "python":
            return _chunk_python(content, file_path)
        if language == "cpp":
            return _chunk_cpp(content, file_path)
        if language == "markdown":
            return _chunk_markdown(content, file_path)
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        return _module_chunks(content.split("\n"), 0, len(content.split("\n")) - 1, file_path)

    # -- Indexing ------------------------------------------------------------
    def index_directory(self, directory_path: str) -> dict:
        """Index (or incrementally update) all code files."""
        directory_path = os.path.abspath(os.path.normpath(directory_path))
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        files = self._scan_directory(directory_path)
        scanned_paths = {f["path"] for f in files}
        indexed = 0
        skipped = 0

        with closing(self._connect()) as conn:
            # Purge entries from old non-canonicalized indexing runs
            # (relative paths or different absolute roots that no longer match)
            with conn:
                conn.execute(
                    "DELETE FROM code_chunks WHERE file_path NOT LIKE ?",
                    (directory_path + os.sep + "%",)
                )
                conn.execute(
                    "DELETE FROM code_fts WHERE file_path NOT LIKE ?",
                    (directory_path + os.sep + "%",)
                )
            with conn:
                for f in files:
                    # Incremental: skip unchanged files (same SHA)
                    rows = conn.execute(
                        "SELECT file_sha FROM code_chunks WHERE file_path = ?",
                        (f["path"],),
                    ).fetchall()
                    if rows and all(r["file_sha"] == f["sha"] for r in rows):
                        skipped += 1
                        continue

                    # Remove old chunks of this file (structure + FTS)
                    conn.execute("DELETE FROM code_fts WHERE file_path = ?", (f["path"],))
                    conn.execute("DELETE FROM code_chunks WHERE file_path = ?", (f["path"],))

                    # Structurally chunk the file and insert
                    # Extract frontmatter for Markdown concept files (LLM-Wiki/OKF)
                    fm_json: str | None = None
                    if f["language"] == "markdown":
                        fm, _fb = _parse_frontmatter(f["content"].split("\n"))
                        if fm:
                            fm_json = json.dumps(fm, ensure_ascii=False)
                    for idx, chunk in enumerate(self._chunk_file(f["language"], f["content"], f["path"])):
                        cur = conn.execute(
                            "INSERT INTO code_chunks "
                            "(chunk_id, file_path, language, chunk_index, line_start, "
                            " line_end, content, symbol_type, symbol_name, "
                            " signature, docstring, frontmatter, file_sha) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (chunk.get("chunk_id"), f["path"], f["language"], idx, chunk["line_start"],
                             chunk["line_end"], chunk["content"],
                             chunk.get("symbol_type"), chunk.get("symbol_name"),
                             chunk.get("signature"), chunk.get("docstring"), fm_json, f["sha"]),
                        )
                        conn.execute(
                            "INSERT INTO code_fts "
                            "(rowid, file_path, language, line_start, line_end, "
                            " symbol_name, signature, docstring, content) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (cur.lastrowid, f["path"], f["language"],
                             chunk["line_start"], chunk["line_end"],
                             chunk.get("symbol_name"), chunk.get("signature"),
                             chunk.get("docstring"), chunk["content"]),
                        )
                    indexed += 1

                # Cleanup: remove deleted/missing files from the index
                stale = self._find_stale_paths(conn, directory_path, scanned_paths)
                for path in stale:
                    conn.execute("DELETE FROM code_fts WHERE file_path = ?", (path,))
                    conn.execute("DELETE FROM code_chunks WHERE file_path = ?", (path,))

        return {"indexed": indexed, "skipped": skipped, "total_files": len(files)}

    @staticmethod
    def _find_stale_paths(conn, directory_path: str, scanned_paths: set) -> list:
        """Find indexed paths under directory_path that no longer exist."""
        prefix = directory_path + os.sep
        # Escape LIKE special chars in the path (backslash as ESCAPE char)
        pattern = (
            prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            + "%"
        )
        stale = []
        for row in conn.execute(
            "SELECT DISTINCT file_path FROM code_chunks "
            "WHERE file_path LIKE ? ESCAPE '\\'",
            (pattern,),
        ):
            if row["file_path"] not in scanned_paths:
                stale.append(row["file_path"])
        return stale

    # -- Query (hybrid: FTS/bm25 + exact identifier boost) ------------------
    @staticmethod
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

    def query(self, query: str, top_k: int = 3, semantic: bool = False) -> list:
        """Hybrid search: FTS5/bm25 candidates + re-ranking by exact hits.

        Fallback for short queries (< 3 chars): LIKE-based search on
        symbol_name, since the trigram tokenizer does not match short tokens.

        Args:
            query: search query.
            top_k: number of results.
            semantic: if True, additional re-ranking via character n-gram
                cosine similarity. Requires no external packages.
        """
        if not query or not query.strip():
            return []
        match_expr = self._build_match_expr(query)
        if not match_expr:
            return self._query_like_fallback(query, top_k)
        with closing(self._connect()) as conn:
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
            rows = _semantic_rerank(query, rows, top_k)

        return rows[:top_k]

    def _query_like_fallback(self, query: str, top_k: int = 3) -> list:
        """LIKE fallback for short queries (< 3 chars per token).

        Searches symbol_name, file_path and content via LIKE.
        """
        q = query.strip().lower()
        if not q:
            return []
        like_pattern = "%" + q + "%"
        with closing(self._connect()) as conn:
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

    # -- Wiki symbol query ---------------------------------------------------
    def query_wiki(self, query: str, max_results: int = 12) -> list:
        """Symbol-based search in the Code-Wiki (name/signature/docstring)."""
        tokens = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query) if len(t) >= 3]
        if not tokens:
            return self._query_wiki_like(query, max_results)
        match_expr = " AND ".join('"' + t + '"' for t in tokens)
        with closing(self._connect()) as conn:
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

    def _query_wiki_like(self, query: str, max_results: int = 12) -> list:
        """LIKE fallback for query_wiki on short queries (< 3 chars)."""
        like = "%" + query.strip().lower() + "%"
        with closing(self._connect()) as conn:
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

    # -- Formatting ----------------------------------------------------------
    @staticmethod
    def chunk_ref(r) -> str:
        """Stable short reference for a chunk: [wogd_ddsp_<hash>]."""
        return f"[{r.get('chunk_id') or r.get('id') or '?'}]"

    @staticmethod
    def format_results(results: list, query: str, format: str = "text") -> str:
        """Format search results as a readable Markdown block for the chat.

        `format` controls the context richness (token optimization):
          - "text":    full Markdown output with code snippets
          - "compact": one line per hit (ID, path, lines, symbol) -
                       full content only via `get_rag_chunk(<id>)`
          - "json":    machine-readable JSON (structured hits incl. IDs)
        """
        if not results:
            return (
                f"No hits in the RAG database for: '{query}'\n"
                "Tip: run `index_project_code` on the project directory first."
            )
        if format == "json":
            return ProjectRAG.format_json(results, query)
        if format == "compact":
            return ProjectRAG.format_compact(results, query)
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
                f"{ProjectRAG.chunk_ref(r)}"
            )
            lines.append(f"    Language: {lang}")
            if r.get("symbol_name"):
                lines.append(f"    Symbol: {r['symbol_name']} ({r.get('symbol_type')})")
            if r.get("signature"):
                lines.append(f"    Signature: {r['signature']}")
            lines.append(f"    ```{lang}\n{indented}\n    ```")
        return "\n".join(lines)

    @staticmethod
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
                f"{ProjectRAG.chunk_ref(r)} {r['file_path']}:"
                f"{r['line_start']}-{r['line_end']} {sym}{sig}"
            )
        lines.append(
            "Full content of a chunk: call `get_rag_chunk` with its ID."
        )
        return "\n".join(lines)

    @staticmethod
    def format_json(results: list, query: str) -> str:
        """Machine-readable JSON output of the hits (stable fields incl. chunk ID)."""
        payload = {
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
        return json.dumps(payload, ensure_ascii=False, indent=2)

    # -- Wiki generation -----------------------------------------------------
    @staticmethod
    def _file_dependencies(conn, file_path: str, language: str) -> list:
        """Collect imports/#includes of a file from the module chunks."""
        if language == "markdown":
            return []
        rows = conn.execute(
            "SELECT content FROM code_chunks WHERE file_path = ? AND symbol_type = 'module'",
            (file_path,),
        ).fetchall()
        deps = []
        seen = set()
        for r in rows:
            for line in r["content"].splitlines():
                line = line.strip()
                is_dep = (
                    language == "python" and (line.startswith("import ") or line.startswith("from "))
                ) or (
                    language == "cpp" and line.startswith("#include")
                )
                if is_dep and line not in seen:
                    seen.add(line)
                    deps.append(line)
                if len(deps) >= 60:
                    return deps
        return deps

    @staticmethod
    def _find_usages(conn, symbol_name: str, file_path: str) -> list:
        """Find usages of a symbol in the content of other chunks.

        Checks whether `symbol_name` occurs as a whole word in the content
        of chunks from other files (= `used_by` relationship).
        Returns a list of (file_path, line_start, symbol_type, chunk_id).
        """
        if not symbol_name or len(symbol_name) < 3:
            return []
        rows = conn.execute(
            """
            SELECT DISTINCT c.file_path, c.line_start, c.symbol_type, c.chunk_id
            FROM code_chunks c
            WHERE c.file_path != ?
              AND c.chunk_id IS NOT NULL
              AND c.content LIKE ?
            LIMIT 20
            """,
            (file_path, f"%{symbol_name}%"),
        ).fetchall()
        # Post-filter on whole words (no substring hits like "init" in "initialized")
        pattern = re.compile(r"(?<!\w)" + re.escape(symbol_name) + r"(?!\w)")
        result = []
        seen = set()
        for r in rows:
            key = (r["file_path"], r["line_start"])
            if key in seen:
                continue
            seen.add(key)
            # Fetch the content for verification
            chunk = conn.execute(
                "SELECT content FROM code_chunks WHERE chunk_id = ?",
                (r["chunk_id"],),
            ).fetchone()
            if chunk and pattern.search(chunk["content"]):
                result.append(dict(r))
        return result[:10]

    def generate_wiki(self, wiki_path: str = WIKI_PATH) -> dict:
        """Generate the Code-Wiki (stable symbol index) as a Markdown file."""
        with closing(self._connect()) as conn:
            files = conn.execute(
                "SELECT DISTINCT file_path, language FROM code_chunks ORDER BY file_path"
            ).fetchall()
            n_chunks = conn.execute("SELECT COUNT(*) AS n FROM code_chunks").fetchone()["n"]
            n_syms = conn.execute(
                "SELECT COUNT(*) AS n FROM code_chunks WHERE symbol_name IS NOT NULL"
            ).fetchone()["n"]

            out = [
                "# wogd-ddsp-trainer Code-Wiki",
                "",
                "_Automatically generated symbol index. Complements "
                "[`doc/architecture.md`](./architecture.md) - manually "
                "maintained architecture knowledge (DDSP model graph, dataset "
                "pipeline, training loop, web UI). See also "
                "[`doc/index.md`](./index.md) for the LLM-Wiki knowledge catalog "
                "and [`doc/log.md`](./log.md) for the chronological changelog._",
                "",
                "<!-- AUTOGENERATED_WIKI_START -->",
                "",
                f"_Automatically generated by `index_project_code` (MCP server). "
                f"{len(files)} files, {n_chunks} chunks, {n_syms} symbols._",
                "",
                "This wiki is the structured symbol index of the codebase. Coding "
                "agents read it once per session as stable context (prompt-cache "
                "friendly) and always verify details against the real source code "
                "(path + line numbers).",
                "",
                "## Table of contents",
            ]
            for f in files:
                out.append(f"- [`{f['file_path']}`](#{_wiki_anchor(f['file_path'])})")
            out.append("")

            for f in files:
                out.append(f"## {f['file_path']}")
                out.append("")
                out.append(f"- Language: `{f['language']}`")
                # Frontmatter metadata for Markdown concept files (LLM-Wiki/OKF)
                if f["language"] == "markdown":
                    fm_row = conn.execute(
                        "SELECT frontmatter FROM code_chunks "
                        "WHERE file_path = ? AND symbol_type = 'frontmatter' "
                        "LIMIT 1",
                        (f["file_path"],),
                    ).fetchone()
                    if fm_row and fm_row["frontmatter"]:
                        try:
                            fm = json.loads(fm_row["frontmatter"])
                            out.append(f"- Type: `{fm.get('type', '?')}`")
                            out.append(f"- Status: `{fm.get('status', '?')}`")
                            if fm.get("stale_after"):
                                out.append(f"- Stale after: `{fm['stale_after']}`")
                            if fm.get("description"):
                                out.append(f"- Description: {fm['description'][:160]}")
                            if fm.get("generated") and isinstance(fm["generated"], dict):
                                out.append(f"- Generated: {fm['generated'].get('by', '?')} @ {fm['generated'].get('at', '?')}")
                        except (json.JSONDecodeError, KeyError):
                            pass
                deps = self._file_dependencies(conn, f["file_path"], f["language"])
                if deps:
                    out.append("- Dependencies: " + ", ".join(deps))
                syms = conn.execute(
                    """
                    SELECT symbol_type, symbol_name, signature, docstring,
                           line_start, line_end
                    FROM code_chunks
                    WHERE file_path = ? AND symbol_name IS NOT NULL
                    ORDER BY line_start
                    """,
                    (f["file_path"],),
                ).fetchall()
                out.append("")
                if not syms:
                    out.append("(no named symbols - only text/Markdown)")
                else:
                    out.append("Symbols:")
                    for s in syms:
                        kind = s["symbol_type"] or ""
                        sig = (s["signature"] or "").replace("|", "\\|")
                        doc_lines = (s["docstring"] or "").strip().splitlines()
                        doc1 = doc_lines[0][:120] if doc_lines else ""
                        entry = (
                            f"- `{s['symbol_name']}` ({kind}, "
                            f"lines {s['line_start']}-{s['line_end']}) - {sig}"
                        )
                        if doc1:
                            entry += f" - {doc1}"
                        out.append(entry)
                        # used_by: symbols from other files that reference this one
                        used_by = self._find_usages(conn, s["symbol_name"], f["file_path"])
                        if used_by:
                            for u in used_by:
                                out.append(
                                    f"  - *used by* `{u['file_path']}:{u['line_start']}` "
                                    f"({u['symbol_type'] or '?'}) [{u['chunk_id']}]"
                                )
                out.append("")

        out_dir = os.path.dirname(os.path.abspath(wiki_path))
        os.makedirs(out_dir, exist_ok=True)
        with open(wiki_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n")
        return {"path": wiki_path, "files": len(files), "chunks": n_chunks, "symbols": n_syms}


def _wiki_anchor(path: str) -> str:
    """Build a GitHub-style Markdown anchor from a file path."""
    base = os.path.splitext(os.path.basename(path))[0].lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


# RAG instance is kept global so all tools use the same database.
_rag = ProjectRAG()


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
        wiki = _rag.generate_wiki(WIKI_PATH)
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
            (one line per hit, token-sparing) or "json" (machine-readable,
            incl. chunk_id).
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
    results = _rag.query(query, top_k=top_k, semantic=semantic)
    return _rag.format_results(results, query, format=format)


@mcp.tool()
def get_rag_chunk(chunk_id: str) -> str:
    """Return the full content of a single RAG chunk (transient).

    Complement to `query_code_rag`/`query_code_wiki`: in compact mode these
    tools return only short references ([wogd_ddsp_<id>]). This function returns
    the full code/text of a chunk - only when it is actually needed in detail
    during reasoning (avoids unnecessary context dumping).

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
        f"Chunk {ProjectRAG.chunk_ref(r)}: {r['file_path']} "
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
            symbol) or "json" (machine-readable, incl. chunk_id).

    Returns:
        Found symbols with file path, line numbers, signature and docstring.
    """
    if not _rag_has_data():
        return (
            "The RAG database is empty.\n"
            "Run `index_project_code` on the project directory first."
        )
    rows = _rag.query_wiki(query, max_results)
    if not rows:
        return (
            f"No wiki symbols for: '{query}'\n"
            "Tip: `query_code_wiki` searches symbol names/signatures. For "
            "full text in implementation code use `query_code_rag`."
        )
    if format == "json":
        return ProjectRAG.format_json(rows, query)
    if format == "compact":
        return ProjectRAG.format_compact(rows, query)
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
